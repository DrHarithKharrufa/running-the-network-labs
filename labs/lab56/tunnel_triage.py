#!/usr/bin/env python3
"""Lab 56.1 --- what the evidence about a tunnel does and does not support.

THE DEFECT THIS REPLACES. The shipped version of this lab took seven booleans,
walked a fixed order, and returned "tunnel healthy -- traffic should pass" when
none of its four conditions fired. Three things were wrong with that, and all
three are the same mistake wearing different clothes:

  1. IT DECLARED HEALTH FROM IGNORANCE. Nothing in its input could establish
     that traffic passes; "healthy" was what it printed when it had run out of
     faults it knew how to detect. An operator reads that as an all-clear.
  2. IT COULD NOT TELL "NOT OBSERVED" FROM "OBSERVED ABSENT". Every field was a
     plain bool, so an unknown became a False and a False became a diagnosis.
  3. IT TREATED A MITIGATION AS PROOF THE FAULT WAS GONE. `mss_clamped=True`
     switched the MTU check off entirely. MSS clamping rewrites one option in
     the TCP handshake. It does nothing for UDP, QUIC, or anything else that
     never negotiates an MSS, so a clamped tunnel with a black-holed path MTU
     looks perfect here and still breaks the DNS, the VPN-in-VPN and the video.

The fixture assumes fresh IKE-established SAs, contemporaneous observations
of the same peer, direction, selectors and path, and no size-selective policy.
Manual SAs, retained SAs across snapshots and policies that discriminate by
size can violate these assumptions without an impossible real network.

This version reports EVIDENCE, HYPOTHESES and EXCLUSIONS, and has no verdict
called "healthy". The strongest thing it will say is that the data path was
CONFIRMED for the traffic you actually tested, at the time you tested it, and it
will only say that when counters in both directions and both a TCP and a non-TCP
application were observed working.

    python3 tunnel_triage.py              # the shipped cases
    python3 tunnel_triage.py --json
    python3 tunnel_triage.py --prove      # exhaustive reachability of every rule
    python3 test_tunnel_triage.py
"""
import itertools
import json
import sys

UNKNOWN = 'unknown'

ROUTE_BASED = 'route-based'
POLICY_BASED = 'policy-based'
MODES = (ROUTE_BASED, POLICY_BASED)


class TriageError(ValueError):
    """The input cannot be reasoned about. Raised, never worked around."""


# ---------------------------------------------------------------------------
# The observations. Each one names the class of command that yields it, because
# a report that asks for evidence without saying where to get it is a riddle.
# ---------------------------------------------------------------------------

OBSERVATIONS = {
    'ike_sa': 'an established IKE (phase 1) SA with this peer exists '
              '[show crypto ikev2 sa / show vpn ike-sa / show ipsec ike-sa]',
    'child_sa_out': 'an OUTBOUND Child/phase 2 SA is installed, with an SPI '
                    '[show crypto ipsec sa, outbound esp sas]',
    'child_sa_in': 'an INBOUND Child/phase 2 SA is installed, with an SPI '
                   '[show crypto ipsec sa, inbound esp sas]',
    'selectors_agree': 'the two ends agree on the traffic selectors / proxy IDs '
                       '[compare both ends; a mismatch often still forms an IKE SA]',
    'encaps_increasing': 'the outbound ESP packet counter rises while the user retries '
                         '[show crypto ipsec sa twice, compare #pkts encaps]',
    'decaps_increasing': 'the inbound ESP packet counter rises '
                         '[show crypto ipsec sa twice, compare #pkts decaps]',
    'route_into_tunnel': 'a route for the remote prefix points at the tunnel interface '
                         '[show ip route <remote>; route-based designs only]',
    'reverse_route_present': 'the FAR end has a route back for the local prefix '
                             '[same command, run at the other site]',
    'crypto_acl_match': 'the two crypto ACLs are exact mirrors '
                        '[show run | section crypto map; policy-based designs only]',
    'post_decrypt_permitted': 'the firewall permits the decrypted traffic, not just IKE/ESP '
                              '[policy lookup for the inner 5-tuple, both directions]',
    'nat_exempted': 'tunnel traffic is exempt from NAT at both ends '
                    '[NAT rule order; a NAT applied before crypto changes the selectors]',
    'small_packets_pass': 'small pings across the tunnel succeed (inner source and destination)',
    'large_df_packets_pass': 'large DF-set packets across the tunnel succeed',
    'ptb_received': 'ICMP fragmentation-needed / packet-too-big reaches the sender '
                    '[capture at the sender; filtered ICMP is why PMTUD black-holes]',
    'mss_clamped': 'an MSS clamp is configured on the tunnel interface',
    'tcp_app_works': 'a TCP application through the tunnel completes',
    'udp_app_works': 'a UDP or QUIC application through the tunnel completes',
}

# ---------------------------------------------------------------------------
# Consistency constraints for this fixture, not all working IPsec systems. The model REFUSES these rather than diagnosing them, because
# an input that cannot happen means the observations were misread, and a
# diagnosis drawn from misread observations is worse than no diagnosis.
# Each is (name, requirement-dict, why).
# ---------------------------------------------------------------------------

IMPOSSIBLE = (
    ('encaps-without-outbound-sa',
     {'encaps_increasing': True, 'child_sa_out': False},
     'a packet cannot be encapsulated by an outbound SA that is not installed; '
     're-read the SA output, you are probably looking at the wrong peer or VRF'),
    ('decaps-without-inbound-sa',
     {'decaps_increasing': True, 'child_sa_in': False},
     'a packet cannot be decapsulated by an inbound SA that is not installed'),
    ('child-sa-without-ike',
     {'ike_sa': False, 'child_sa_out': True},
     'outside the fresh, contemporaneous IKE fixture: check snapshots, peer and '
     'SA lifecycle; manual SAs and retained cross-snapshot SAs are not covered'),
    ('child-sa-in-without-ike',
     {'ike_sa': False, 'child_sa_in': True},
     'as above, for the inbound SA'),
    ('large-passes-small-fails',
     {'small_packets_pass': False, 'large_df_packets_pass': True},
     'outside the same-path, no-size-selective-policy fixture; check policy, '
     'selectors, payload, times and measurement comparability before diagnosis'),
)

# ---------------------------------------------------------------------------
# The rules. A rule fires only when EVERY observation it requires is KNOWN and
# matches. If any is UNKNOWN the rule is undecided and the missing observation
# is reported as evidence needed --- it is never assumed either way.
#
# verdict is one of:
#   FAULT        the evidence identifies this fault
#   HYPOTHESIS   consistent with the evidence; other explanations remain
#   WARNING      not a fault by itself, but it invalidates a conclusion someone
#                is about to draw
# ---------------------------------------------------------------------------

FAULT, HYPOTHESIS, WARNING = 'FAULT', 'HYPOTHESIS', 'WARNING'

RULES = (
    dict(id='no-ike-sa', verdict=FAULT,
         needs={'ike_sa': False},
         says='There is no IKE SA, so nothing is "up". Work the establishment '
              'problem --- proposal mismatch, identity or credential mismatch, '
              'UDP/500 and UDP/4500 blocked on the path, or the peer not '
              'listening --- and do not look at Child SAs yet.',
         note='DPD settings do not prevent establishment; they decide how a peer '
              'that has gone away is noticed. A DPD difference is not a cause of '
              'this symptom.'),

    dict(id='ike-up-no-child', verdict=FAULT,
         needs={'ike_sa': True, 'child_sa_out': False},
         says='The IKE SA is established and no outbound Child SA exists. This is '
              'the exact case that reads as "up" on a dashboard and carries '
              'nothing. Look at the Child SA proposal and the traffic selectors, '
              'not at routing.'),

    dict(id='one-way-sa', verdict=FAULT,
         needs={'child_sa_out': True, 'child_sa_in': False},
         says='An outbound Child SA exists with no inbound one. SAs are '
              'unidirectional and come in pairs; one direction alone means the '
              'peer never installed or never signalled its half.'),

    dict(id='selector-mismatch', verdict=FAULT,
         needs={'ike_sa': True, 'selectors_agree': False},
         says='The traffic selectors do not agree. Traffic that does not match an '
              'installed selector is not encrypted at all --- it leaves in clear '
              'or is dropped, depending on the platform.'),

    dict(id='no-route-into-tunnel', verdict=FAULT, mode=ROUTE_BASED,
         needs={'route_into_tunnel': False},
         says='Route-based design with no route for the remote prefix pointing at '
              'the tunnel interface: traffic never reaches the tunnel, so the SA '
              'stays idle and every counter stays at zero.'),

    dict(id='no-reverse-route', verdict=FAULT,
         needs={'reverse_route_present': False},
         says='The far end has no route back. Forward traffic is encrypted and '
              'delivered; the reply is not, and the user sees a one-way tunnel, '
              'which looks identical to a drop.'),

    dict(id='crypto-acl-mismatch', verdict=FAULT, mode=POLICY_BASED,
         needs={'crypto_acl_match': False},
         says='Policy-based design whose crypto ACLs are not mirrors. Each end '
              'protects a different set of flows, so some traffic is encrypted in '
              'one direction and discarded at the other.'),

    dict(id='nat-not-exempted', verdict=HYPOTHESIS,
         needs={'nat_exempted': False},
         says='Tunnel traffic is not exempt from NAT. If NAT is applied before the '
              'crypto lookup, the translated address no longer matches the '
              'selector and the flow silently leaves the tunnel.'),

    dict(id='post-decrypt-blocked', verdict=FAULT,
         needs={'decaps_increasing': True, 'post_decrypt_permitted': False},
         says='Packets are arriving and being decrypted --- the inbound counter is '
              'moving --- and the firewall is dropping them after decryption. The '
              'tunnel is working; the policy is not.'),

    dict(id='encaps-no-decaps', verdict=HYPOTHESIS,
         needs={'encaps_increasing': True, 'decaps_increasing': False},
         says='Outbound encapsulation is happening and nothing is coming back. '
              'Either the far end is not replying (inner routing, inner policy, or '
              'the application) or the return ESP is being lost on the path. '
              'Capture ESP at the far end to tell those apart: this counter pair '
              'alone cannot.'),

    dict(id='mtu-black-hole', verdict=FAULT,
         needs={'small_packets_pass': True, 'large_df_packets_pass': False},
         says='Small packets cross and large DF packets do not. That is a path MTU '
              'fault: the encapsulation overhead makes the inner MTU smaller than '
              'the endpoints believe. Compute the real figure (lab 56.2) and set '
              'the tunnel MTU accordingly.'),

    dict(id='pmtud-blackholed', verdict=FAULT,
         needs={'large_df_packets_pass': False, 'ptb_received': False},
         says='Large DF packets are dropped AND no ICMP packet-too-big is reaching '
              'the sender, so path MTU discovery cannot work. Somebody is '
              'filtering ICMP. This is the fault that makes MTU problems '
              'intermittent and host-specific.'),

    # The rule the shipped lab could not express, because a clamp switched its
    # MTU check off instead of switching this one on.
    dict(id='clamp-hides-mtu-fault', verdict=WARNING,
         needs={'mss_clamped': True, 'large_df_packets_pass': False},
         says='An MSS clamp is in place and large DF packets still fail. The clamp '
              'rewrites the MSS option in the TCP handshake and nothing else, so '
              'it has hidden the fault from TCP while leaving it in place for UDP, '
              'QUIC, IPsec-in-IPsec, and any tunnel carried inside this one. Do '
              'not read "TCP works now" as "the MTU is right".'),

    dict(id='clamp-only-tcp-fixed', verdict=FAULT,
         needs={'mss_clamped': True, 'tcp_app_works': True, 'udp_app_works': False},
         says='TCP works and UDP does not, with a clamp configured. This is the '
              'clamp doing exactly what it does: protecting the protocol that '
              'negotiates a segment size and no other. Fix the MTU itself.'),

    dict(id='works-but-not-through-the-tunnel', verdict=WARNING,
         needs={'tcp_app_works': True, 'encaps_increasing': False},
         says='The application works and the outbound ESP counter is not moving, so '
              'this traffic is NOT going through the tunnel. Something else is '
              'carrying it --- a default route, a split-tunnel exclusion, a second '
              'path. Whatever you conclude about the tunnel from this test is '
              'about the other path.'),
)


# ---------------------------------------------------------------------------

def _validate(obs, mode):
    if not isinstance(obs, dict):
        raise TriageError('observations must be a dict')
    unknown_keys = sorted(set(obs) - set(OBSERVATIONS))
    if unknown_keys:
        raise TriageError('unrecognised observation(s): %s --- add them to '
                          'OBSERVATIONS with the command that yields them, or '
                          'correct the spelling' % ', '.join(unknown_keys))
    for k, v in obs.items():
        if v is not True and v is not False and v != UNKNOWN:
            raise TriageError('observation %r must be True, False or %r, not %r. '
                              'There is no fourth state, and an unknown must not '
                              'be written as False.' % (k, UNKNOWN, v))
    if mode != UNKNOWN and mode not in MODES:
        raise TriageError('mode must be one of %s or %r, not %r --- an '
                          'unrecognised mode would silently skip the checks that '
                          'depend on it' % (MODES, UNKNOWN, mode))
    for name, req, why in IMPOSSIBLE:
        if all(obs.get(k, UNKNOWN) is v for k, v in req.items()):
            raise TriageError('inconsistent observations (%s): %s' % (name, why))


def analyse(observations=None, mode=UNKNOWN):
    """Return what the evidence supports. Never returns a clean bill of health."""
    if observations is not None and not isinstance(observations, dict):
        raise TriageError('observations must be a dict, not %s --- an empty list '
                          'is falsy and would otherwise be read as "nothing '
                          'observed", which is the very confusion this model '
                          'exists to prevent' % type(observations).__name__)
    obs = dict(observations or {})
    _validate(obs, mode)
    known = {k: v for k, v in obs.items() if v != UNKNOWN}

    findings, blocked, excluded = [], [], []
    for rule in RULES:
        if rule.get('mode') and mode != rule['mode']:
            if mode == UNKNOWN:
                blocked.append(dict(rule_id=rule['id'], missing=['mode'],
                                    how='the design is route-based or policy-based; '
                                        'the check differs and cannot be guessed'))
            continue
        missing = [k for k in rule['needs'] if k not in known]
        if missing:
            blocked.append(dict(rule_id=rule['id'], missing=sorted(missing),
                                how='; '.join(OBSERVATIONS[k] for k in sorted(missing))))
            continue
        if all(known[k] is v for k, v in rule['needs'].items()):
            findings.append(dict(id=rule['id'], verdict=rule['verdict'],
                                 says=rule['says'], note=rule.get('note'),
                                 rested_on={k: known[k] for k in rule['needs']}))
        else:
            excluded.append(dict(id=rule['id'],
                                 because={k: known[k] for k in rule['needs']
                                          if known[k] is not rule['needs'][k]}))

    # The only positive statement available, and it is narrow on purpose.
    confirm = ('encaps_increasing', 'decaps_increasing', 'tcp_app_works', 'udp_app_works')
    missing_for_confirm = [k for k in confirm if known.get(k) is not True]
    if missing_for_confirm:
        data_path = 'NOT CONFIRMED'
        data_path_why = ('the data path is confirmed only by counters rising in '
                         'BOTH directions and by both a TCP and a non-TCP '
                         'application completing. Still outstanding: %s'
                         % ', '.join(missing_for_confirm))
    else:
        data_path = 'CONFIRMED FOR WHAT WAS TESTED'
        data_path_why = ('both counters moved and both a TCP and a non-TCP '
                         'application completed. That is a statement about the '
                         'traffic you tested at the time you tested it, not about '
                         'the tunnel in general.')

    return {
        'mode': mode,
        'findings': sorted(findings, key=lambda f: (f['verdict'] != FAULT, f['id'])),
        'evidence_needed': sorted(blocked, key=lambda b: b['rule_id']),
        'excluded': sorted(excluded, key=lambda e: e['id']),
        'data_path': data_path,
        'data_path_why': data_path_why,
        'observations_known': len(known),
        'observations_total': len(OBSERVATIONS),
    }


# ---------------------------------------------------------------------------
# The fourth question: can each check ever fire?
# Rules are evaluated independently, so reachability is only interesting because
# of the IMPOSSIBLE constraints. Enumerate every tri-state assignment over the
# observations those constraints couple together, keep the consistent ones, and
# ask of each rule whether ANY of them satisfies it. A rule that no consistent
# input can satisfy is dead code pretending to be a control.
# ---------------------------------------------------------------------------

COUPLED = sorted({k for _, req, _ in IMPOSSIBLE for k in req})


def prove_every_rule_can_fire():
    states = (True, False, UNKNOWN)
    consistent = []
    for combo in itertools.product(states, repeat=len(COUPLED)):
        cand = dict(zip(COUPLED, combo))
        if any(all(cand.get(k, UNKNOWN) is v for k, v in req.items())
               for _, req, _ in IMPOSSIBLE):
            continue
        consistent.append(cand)

    report = []
    for rule in RULES:
        wanted_mode = rule.get('mode') or ROUTE_BASED
        witness = None
        for cand in consistent:
            trial = dict(cand)
            clash = False
            for k, v in rule['needs'].items():
                if k in trial and trial[k] is not v:
                    clash = True
                    break
                trial[k] = v
            if clash:
                continue
            if any(all(trial.get(k, UNKNOWN) is v for k, v in req.items())
                   for _, req, _ in IMPOSSIBLE):
                continue
            res = analyse(trial, wanted_mode)
            if any(f['id'] == rule['id'] for f in res['findings']):
                witness = trial
                break
        report.append(dict(rule_id=rule['id'], can_fire=witness is not None,
                           witness=witness))
    return dict(coupled=COUPLED, consistent_states=len(consistent),
                enumerated=len((True, False, UNKNOWN)) ** len(COUPLED),
                rules=report)


# ---------------------------------------------------------------------------

CASES = {
    'the dashboard says up, nothing crosses': dict(
        mode=ROUTE_BASED,
        obs={'ike_sa': True, 'child_sa_out': False, 'child_sa_in': False,
             'route_into_tunnel': True}),
    'small pings fine, web pages hang half-loaded': dict(
        mode=ROUTE_BASED,
        obs={'ike_sa': True, 'child_sa_out': True, 'child_sa_in': True,
             'selectors_agree': True, 'route_into_tunnel': True,
             'reverse_route_present': True, 'encaps_increasing': True,
             'decaps_increasing': True, 'small_packets_pass': True,
             'large_df_packets_pass': False, 'ptb_received': False,
             'mss_clamped': False}),
    'somebody clamped the MSS and called it fixed': dict(
        mode=ROUTE_BASED,
        obs={'ike_sa': True, 'child_sa_out': True, 'child_sa_in': True,
             'selectors_agree': True, 'route_into_tunnel': True,
             'reverse_route_present': True, 'encaps_increasing': True,
             'decaps_increasing': True, 'small_packets_pass': True,
             'large_df_packets_pass': False, 'ptb_received': False,
             'mss_clamped': True, 'tcp_app_works': True, 'udp_app_works': False}),
    'the ticket says "tunnel is up", and that is all we have': dict(
        mode=UNKNOWN, obs={'ike_sa': True}),
    'it works --- but the counters say it is not the tunnel': dict(
        mode=ROUTE_BASED,
        obs={'ike_sa': True, 'child_sa_out': True, 'child_sa_in': True,
             'encaps_increasing': False, 'tcp_app_works': True}),
}


def report(out=None):
    # Bound at call time, not at definition time: a default of sys.stdout
    # captures the stream as it was when the module was imported, so a caller
    # that redirects stdout gets output anyway.
    out = sys.stdout if out is None else out
    out.write("Lab 56.1 --- what the evidence supports about a tunnel\n")
    out.write("=" * 68 + "\n\n")
    for name, case in CASES.items():
        res = analyse(case['obs'], case['mode'])
        out.write('CASE: %s\n' % name)
        out.write('  design: %s   observations supplied: %d of %d\n'
                  % (res['mode'], res['observations_known'], res['observations_total']))
        if res['findings']:
            for f in res['findings']:
                out.write('  %-10s %s\n' % (f['verdict'], f['id']))
                out.write('             %s\n' % _wrap(f['says'], 13))
                if f['note']:
                    out.write('             note: %s\n' % _wrap(f['note'], 19))
        else:
            out.write('  (no rule fired on the evidence supplied)\n')
        out.write('  DATA PATH: %s\n' % res['data_path'])
        out.write('             %s\n' % _wrap(res['data_path_why'], 13))
        if res['evidence_needed']:
            out.write('  NEXT OBSERVATIONS that would decide something '
                      '(%d checks are waiting on evidence):\n'
                      % len(res['evidence_needed']))
            seen = set()
            for b in res['evidence_needed'][:6]:
                for m in b['missing']:
                    if m in seen:
                        continue
                    seen.add(m)
                    out.write('    - %s: %s\n' % (m, _wrap(
                        OBSERVATIONS.get(m, 'route-based or policy-based'), 6)))
        out.write('\n')
    out.write('Nothing above is a clean bill of health. There is no verdict in\n')
    out.write('this model called "healthy": absence of a detected fault is not\n')
    out.write('evidence that traffic passes, and only the data-path line says\n')
    out.write('anything positive, for exactly the traffic that was tested.\n')


def _wrap(text, indent, width=74):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width - indent:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def main(argv):
    if '--json' in argv:
        print(json.dumps({n: analyse(c['obs'], c['mode']) for n, c in CASES.items()},
                         indent=1, sort_keys=True))
        return 0
    if '--prove' in argv:
        p = prove_every_rule_can_fire()
        print('Reachability of every rule, by exhaustion over the observations')
        print('that the impossibility constraints couple together.\n')
        print('  coupled observations : %s' % ', '.join(p['coupled']))
        print('  assignments enumerated: %d' % p['enumerated'])
        print('  of those, consistent  : %d' % p['consistent_states'])
        print()
        for r in p['rules']:
            print('  %-32s %s' % (r['rule_id'], 'CAN FIRE' if r['can_fire']
                                  else 'DEAD CODE --- no consistent input reaches it'))
        dead = [r['rule_id'] for r in p['rules'] if not r['can_fire']]
        print()
        print('  %d rule(s) unreachable' % len(dead) if dead
              else '  every rule is reachable from a consistent observation set')
        return 1 if dead else 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
