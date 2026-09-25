#!/usr/bin/env python3
"""Lab 52.3 --- revoking ONE person, executed with real OpenSSH certificates.

WHY THIS LAB EXISTS
-------------------
The chapter recommended SSH certificates over raw authorised-keys files, on the
grounds that removing a leaver from a thousand devices is a scavenger hunt.
That reasoning is right and the conclusion it invites is wrong:

    "revoke the certificate authority relationship and the leaver is out"

Removing the CA from a device's TrustedUserCAKeys does not revoke a person. It removes that trust path for every certificate from the CA on the
changed server. Alternative trust/authentication paths may still work, and
existing sessions are not killed. The fixture assumes this is the only path. Revoking one holder needs a key revocation list distributed to every
device that trusts the CA, or certificates short-lived enough that waiting is
acceptable. Both are real answers; neither is free; and the difference between
them is an operational commitment, not a configuration line.

This runs it. Real Ed25519 keys, a real CA, real OpenSSH certificates and a real
KRL, all generated in a temporary directory and destroyed afterwards.

    python3 ssh_revocation.py
    python3 ssh_revocation.py --json
    python3 test_ssh_revocation.py

Nothing connects to anything: no sshd runs, no network socket is opened and no
authentication is performed. This demonstrates what the CERTIFICATE TOOLING
says about a credential, which is the part of the claim that was wrong. Whether
a given server enforces what the tooling reports is that server's
configuration, and it is not tested here.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


class RevocationError(RuntimeError):
    """The described certificate operation could not be carried out."""


def _run(args, cwd, check=True):
    # stdin is closed deliberately: ssh-keygen prompts interactively for a
    # filename or a passphrase on several error paths, and a lab that hangs
    # waiting for a human is worse than one that fails.
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       timeout=60, stdin=subprocess.DEVNULL)
    if check and r.returncode != 0:
        raise RevocationError('%s failed (%d): %s'
                              % (' '.join(args), r.returncode, r.stderr.strip()))
    return r


def have_ssh_keygen():
    return shutil.which('ssh-keygen') is not None


def keygen_version():
    """Read the OpenSSH version without tripping an interactive prompt.

    NOTE for anyone extending this: `ssh-keygen -h` is NOT a help flag. It is
    accepted as an option and ssh-keygen then proceeds to generate a key,
    prompting for a filename --- which hangs. Ask `ssh -V` instead, and keep
    stdin closed regardless.
    """
    if not have_ssh_keygen():
        return None
    for cmd in (['ssh', '-V'], ['ssh-keygen', '--bogus-option']):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                               stdin=subprocess.DEVNULL)
        except Exception:
            continue
        m = re.search(r'OpenSSH[_ ]([\w.]+)', (r.stderr or '') + (r.stdout or ''))
        if m:
            return 'OpenSSH ' + m.group(1)
    return 'ssh-keygen (version not reported)'


def make_ca(d, name='ca'):
    _run(['ssh-keygen', '-q', '-t', 'ed25519', '-f', name, '-N', '',
          '-C', 'lab52 temporary CA'], d)
    return name


def make_user(d, user):
    _run(['ssh-keygen', '-q', '-t', 'ed25519', '-f', user, '-N', '',
          '-C', user], d)
    return user


def issue(d, ca, user, validity='+52w', principal=None):
    """Issue a certificate. validity is ssh-keygen's -V expression."""
    _run(['ssh-keygen', '-q', '-s', ca, '-I', user, '-n', principal or user,
          '-V', validity, user + '.pub'], d)
    return user + '-cert.pub'


def describe(d, cert):
    r = _run(['ssh-keygen', '-L', '-f', cert], d)
    out = {'key_id': None, 'principals': None, 'valid': None, 'signing_ca': None}
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith('Key ID:'):
            out['key_id'] = line.split('"')[1] if '"' in line else line
        elif line.startswith('Signing CA:'):
            out['signing_ca'] = line.split(None, 2)[2][:60]
        elif line.startswith('Valid:'):
            out['valid'] = line.split(':', 1)[1].strip()
        elif line.startswith('Principals:'):
            out['principals'] = 'listed'
    return out


def build_krl(d, krl, certs):
    _run(['ssh-keygen', '-k', '-f', krl] + list(certs), d)
    return krl


def krl_says_revoked(d, krl, cert):
    """ssh-keygen -Q exits non-zero when the KRL revokes the credential."""
    r = _run(['ssh-keygen', '-Q', '-f', krl, cert], d, check=False)
    return r.returncode != 0, r.stdout.strip()


def cert_is_expired(d, cert):
    """Read the validity window ssh-keygen reports, without trusting a clock."""
    info = describe(d, cert)
    v = info['valid'] or ''
    m = re.search(r'from (\S+) to (\S+)', v)
    if not m:
        return None, v
    import datetime as _dt
    end = _dt.datetime.fromisoformat(m.group(2))
    return end < _dt.datetime.now(), v


# ---------------------------------------------------------------------------
# the three answers
# ---------------------------------------------------------------------------
def demo(d):
    ca = make_ca(d)
    team = ['alice', 'bob', 'carol']
    certs = {}
    for u in team:
        make_user(d, u)
        certs[u] = issue(d, ca, u)
    same_ca = len({describe(d, c)['signing_ca'] for c in certs.values()}) == 1

    # ANSWER 1: remove the CA relationship.
    # Nothing is executed here because there is nothing to execute: removing
    # the CA from TrustedUserCAKeys is a server-side edit. What IS checkable is
    # the blast radius, and it is every certificate the CA signed.
    ca_removal = {
        'mechanism': 'delete the CA from TrustedUserCAKeys on every device',
        'who_loses_access': sorted(certs),
        'count': len(certs),
        'leaver': 'alice',
        'others_affected': sorted(set(certs) - {'alice'}),
        'note': 'Every fixture certificate loses this CA trust path on the changed '
                'server. Alternative credentials, other trust paths and existing '
                'sessions are outside this calculation; no server is exercised.',
    }

    # ANSWER 2: a key revocation list.
    krl = build_krl(d, 'team.krl', [certs['alice']])
    revoked = {}
    for u in team:
        is_rev, line = krl_says_revoked(d, krl, certs[u])
        revoked[u] = {'revoked': is_rev, 'tool_output': line}
    krl_answer = {
        'mechanism': 'build a KRL and distribute it to every device that '
                     'trusts the CA',
        'revoked': [u for u in team if revoked[u]['revoked']],
        'still_valid': [u for u in team if not revoked[u]['revoked']],
        'detail': revoked,
        'cost': 'The KRL is a FILE. It works on the devices that have the '
                'current copy, so revocation is now a distribution problem '
                'with the same reach as the CA itself, and a device that '
                'missed the update still accepts the leaver.',
    }

    # ANSWER 3: short-lived certificates.
    make_user(d, 'dave')
    short = issue(d, ca, 'dave', validity='-2w:-1w')
    expired, window = cert_is_expired(d, short)
    make_user(d, 'erin')
    current = issue(d, ca, 'erin', validity='-1h:+8h')
    still_ok, window2 = cert_is_expired(d, current)
    lifetime_answer = {
        'mechanism': 'issue certificates that expire on their own',
        'expired_certificate_window': window,
        'expired_now': expired,
        'current_certificate_window': window2,
        'current_expired_now': still_ok,
        'cost': 'Nothing has to reach the devices, which is the point --- but '
                'the leaver keeps access until the certificate runs out, and '
                'the issuing service is now on the critical path for everyone '
                'logging in, every few hours, for ever.',
    }
    return {'same_ca': same_ca, 'team': team,
            'certificates': {u: describe(d, c) for u, c in certs.items()},
            'ca_removal': ca_removal, 'krl': krl_answer,
            'lifetimes': lifetime_answer}


def build_report():
    if not have_ssh_keygen():
        raise RevocationError(
            'ssh-keygen is not on PATH. This lab executes real OpenSSH '
            'certificate operations and will not simulate them: install '
            'openssh-client and run it again.')
    with tempfile.TemporaryDirectory(prefix='netbook-ssh-') as folder:
        d = folder
        result = demo(d)
    return {
        'tool': keygen_version(),
        'executed': result,
        'evidence_category':
            'LINUX EXECUTION. Real Ed25519 keys, a real CA, real OpenSSH '
            'certificates and a real KRL, generated in a temporary directory '
            'and destroyed with it. No sshd, no socket, no authentication.',
        'caveats': [
            'This shows what the CERTIFICATE TOOLING reports about a '
            'credential. Whether a given server enforces it is that server\'s '
            'configuration --- TrustedUserCAKeys, RevokedKeys, clock accuracy '
            'and principals --- and none of that is tested here.',
            'Removing the CA relationship is a server-side edit with nothing '
            'to execute; what is shown is its blast radius, which is every '
            'certificate that CA signed.',
            'A KRL revokes on the devices holding the CURRENT copy. Its reach '
            'is a distribution problem exactly as large as the CA estate, and '
            'a device that missed the update still accepts the leaver. This '
            'lab does not model distribution.',
            'Short-lived certificates depend on accurate time at the verifier '
            'and put the issuing service on the critical path for every login. '
            'Neither is modelled.',
            'Nothing here evaluates the cryptography of Ed25519 or of the '
            'certificate format, and no attack is attempted.',
        ],
    }


def _wrap(lines, text, indent='  '):
    lines.extend(textwrap.wrap(text, width=74, initial_indent=indent,
                               subsequent_indent=indent))


def report_text(rep):
    e = rep['executed']
    L = []
    L.append('Revoking one person, with real certificates (Chapter 52)')
    L.append('Executed with %s. No server, no socket, no authentication.'
             % (rep['tool'] or 'ssh-keygen'))
    L.append('')
    L.append('A. Three people, one certificate authority')
    L.append('-' * 74)
    for u, c in sorted(e['certificates'].items()):
        L.append('  %-8s key id %-8s valid %s' % (u, c['key_id'], c['valid']))
    L.append('')
    L.append('  All three signed by the same CA: %s' % e['same_ca'])
    L.append('')
    L.append('B. Answer one: remove the CA relationship')
    L.append('-' * 74)
    r = e['ca_removal']
    L.append('  mechanism        %s' % r['mechanism'])
    L.append('  leaver           %s' % r['leaver'])
    L.append('  loses access     %s  (%d people)'
             % (', '.join(r['who_loses_access']), r['count']))
    L.append('  also locked out  %s' % ', '.join(r['others_affected']))
    L.append('')
    _wrap(L, r['note'])
    L.append('')
    L.append('C. Answer two: a key revocation list')
    L.append('-' * 74)
    k = e['krl']
    for u, v in sorted(k['detail'].items()):
        L.append('  %-8s %-9s %s' % (u, 'REVOKED' if v['revoked'] else 'ok',
                                     v['tool_output'][:44]))
    L.append('')
    L.append('  revoked: %s     still valid: %s'
             % (', '.join(k['revoked']), ', '.join(k['still_valid'])))
    L.append('')
    _wrap(L, 'This is the answer the chapter should have given. One person is '
             'out and the rest of the team is unaffected --- which the CA '
             'removal above could not do.')
    L.append('')
    _wrap(L, k['cost'])
    L.append('')
    L.append('D. Answer three: certificates that expire on their own')
    L.append('-' * 74)
    li = e['lifetimes']
    L.append('  expired certificate  %s' % li['expired_certificate_window'])
    L.append('      past its window now: %s' % li['expired_now'])
    L.append('  current certificate  %s' % li['current_certificate_window'])
    L.append('      past its window now: %s' % li['current_expired_now'])
    L.append('')
    _wrap(L, li['cost'])
    L.append('')
    _wrap(L, 'So there are three mechanisms and only two of them revoke a '
             'person. Choosing between the KRL and short lifetimes is a '
             'choice about which operational burden you would rather carry: '
             'distributing a file to every device, or running an issuing '
             'service that every login depends on. "Use certificates" names '
             'neither.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.extend(textwrap.wrap(c, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    a = p.parse_args(argv)
    try:
        rep = build_report()
    except RevocationError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
