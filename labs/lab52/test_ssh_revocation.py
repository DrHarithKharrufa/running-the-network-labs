#!/usr/bin/env python3
"""Checks for ssh_revocation.py.

This lab's claim is about what real OpenSSH tooling does, so the tests drive
that tooling directly rather than trusting the lab's own report. The central
pair is: a KRL built against one certificate must revoke THAT one and leave the
others working. If either half failed the lab would be making its point with a
demonstration that does not demonstrate it.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import ssh_revocation as R

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except R.RevocationError:
        return True
    except Exception:
        return False
    return False


if not R.have_ssh_keygen():
    print('ssh_revocation: SKIPPED, ssh-keygen is not installed')
    sys.exit(0)

check('ssh-keygen is available', R.have_ssh_keygen() is True)
v = R.keygen_version()
check('a version is reported', bool(v))
check('the version mentions OpenSSH or says it could not tell',
      'OpenSSH' in v or 'not reported' in v)

# ===========================================================================
# THE CENTRAL PAIR: a KRL revokes one and only one
# ===========================================================================
with tempfile.TemporaryDirectory(prefix='netbook-ssh-test-') as d:
    ca = R.make_ca(d)
    check('a CA key was written', os.path.exists(os.path.join(d, 'ca')))
    check('a CA public key was written', os.path.exists(os.path.join(d, 'ca.pub')))
    users = ['alice', 'bob', 'carol']
    certs = {}
    for u in users:
        R.make_user(d, u)
        certs[u] = R.issue(d, ca, u)
        check('a certificate was issued for %s' % u,
              os.path.exists(os.path.join(d, certs[u])))
    infos = {u: R.describe(d, c) for u, c in certs.items()}
    for u in users:
        check('%s certificate carries its key id' % u, infos[u]['key_id'] == u)
        check('%s certificate names a signing CA' % u, bool(infos[u]['signing_ca']))
        check('%s certificate has a validity window' % u, bool(infos[u]['valid']))
    check('all three were signed by the same CA',
          len({i['signing_ca'] for i in infos.values()}) == 1)

    krl = R.build_krl(d, 'test.krl', [certs['alice']])
    check('a KRL file was written', os.path.exists(os.path.join(d, krl)))
    rev_alice, out_alice = R.krl_says_revoked(d, krl, certs['alice'])
    rev_bob, out_bob = R.krl_says_revoked(d, krl, certs['bob'])
    rev_carol, _ = R.krl_says_revoked(d, krl, certs['carol'])
    check('the KRL revokes alice', rev_alice is True)
    check('the KRL does NOT revoke bob', rev_bob is False)
    check('the KRL does NOT revoke carol', rev_carol is False)
    check('the tool says REVOKED for alice', 'REVOKED' in out_alice)
    check('the tool says ok for bob', 'ok' in out_bob)
    check('so exactly one of three is revoked',
          sum([rev_alice, rev_bob, rev_carol]) == 1)

    # a KRL revoking two revokes exactly two
    krl2 = R.build_krl(d, 'two.krl', [certs['alice'], certs['bob']])
    revs = [R.krl_says_revoked(d, krl2, certs[u])[0] for u in users]
    check('a KRL naming two certificates revokes exactly two', sum(revs) == 2)
    check('and leaves the third', revs[2] is False)

    # an empty KRL revokes nobody
    krl0 = R.build_krl(d, 'empty.krl', [])
    check('an empty KRL revokes nobody',
          not any(R.krl_says_revoked(d, krl0, certs[u])[0] for u in users))

    # ===========================================================================
    # expiry
    # ===========================================================================
    R.make_user(d, 'dave')
    past = R.issue(d, ca, 'dave', validity='-2w:-1w')
    expired, window = R.cert_is_expired(d, past)
    check('a certificate with a past window reads as expired', expired is True)
    check('and its window is reported', 'to' in window)
    R.make_user(d, 'erin')
    now = R.issue(d, ca, 'erin', validity='-1h:+8h')
    still, window2 = R.cert_is_expired(d, now)
    check('a current certificate does not read as expired', still is False)
    check('the two windows differ', window != window2)
    R.make_user(d, 'frank')
    future = R.issue(d, ca, 'frank', validity='+1w:+2w')
    fut, _ = R.cert_is_expired(d, future)
    check('a not-yet-valid certificate is not reported as expired', fut is False)

    # ===========================================================================
    # error handling
    # ===========================================================================
    check('describing a missing certificate is refused',
          raises(R.describe, d, 'no-such-cert.pub'))
    check('issuing from a missing CA is refused',
          raises(R.issue, d, 'no-such-ca', 'alice'))
    check('a KRL query against a missing file is handled',
          isinstance(R.krl_says_revoked(d, krl, certs['alice']), tuple))

# ===========================================================================
# the lab's own report agrees with the tooling
# ===========================================================================
rep = R.build_report()
e = rep['executed']
check('the report names the tool', bool(rep['tool']))
check('all three certificates share a CA', e['same_ca'] is True)
check('the CA-removal answer locks out everyone',
      len(e['ca_removal']['who_loses_access']) == len(e['team']))
check('and names the others affected',
      set(e['ca_removal']['others_affected']) == set(e['team']) - {'alice'})
check('and that is more than one person',
      len(e['ca_removal']['others_affected']) >= 2)
check('the KRL answer revokes exactly one', len(e['krl']['revoked']) == 1)
check('and leaves the rest valid',
      len(e['krl']['still_valid']) == len(e['team']) - 1)
check('the KRL answer revokes alice', e['krl']['revoked'] == ['alice'])
check('the KRL cost names distribution', 'distribution problem' in e['krl']['cost'])
check('the expiry answer shows an expired certificate',
      e['lifetimes']['expired_now'] is True)
check('and a current one that is not expired',
      e['lifetimes']['current_expired_now'] is False)
check('the expiry cost names the issuing service',
      'critical path' in e['lifetimes']['cost'])
check('the evidence category says Linux execution',
      'LINUX EXECUTION' in rep['evidence_category'])
check('it says no sshd and no socket',
      'No sshd' in rep['evidence_category'])
check('the report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says enforcement is the server configuration',
      any("server's\nconfiguration" in c or "server's configuration" in c
          for c in rep['caveats']))
check('a caveat says a KRL must be distributed',
      any('distribution problem' in c for c in rep['caveats']))
check('a caveat says short lifetimes need accurate time',
      any('accurate time' in c for c in rep['caveats']))
check('the report JSON-serialises', isinstance(json.dumps(rep), str))
text = R.report_text(rep)
check('the text names four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text says only two of three mechanisms revoke a person',
      'only two of them revoke' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'ssh_revocation.py', '--json'],
                     capture_output=True, text=True, timeout=180)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'ssh_revocation.py'],
                       capture_output=True, text=True, timeout=180)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))
check('no temporary key material survives the run',
      not os.path.exists('/tmp/netbook-ssh'))

print('ssh_revocation: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
