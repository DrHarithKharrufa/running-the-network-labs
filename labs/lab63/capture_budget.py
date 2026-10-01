#!/usr/bin/env python3
"""Lab 63.2 --- the capture path, budgeted end to end.

Chapter 63 says a tap does not make the receiving NIC, driver, buffers,
processor or storage lossless, and that mirroring both directions of a fully
utilised 10 Gb/s link into one 10 Gb/s output offers 20 Gb/s to that output.
Both are true and neither is a number you can design against. This lab supplies
the numbers, and three of them are uncomfortable:

  * A 4,096-DESCRIPTOR RING TAKING BOTH DIRECTIONS OF A 10 Gb/s LINK AT
    MINIMUM FRAME SIZE DRAINS IN 138 MICROSECONDS. Any scheduling delay longer
    than that drops packets, behind a tap or not, and the loss appears as a gap
    in the capture rather than as an error.
  * A PASSIVE OPTICAL TAP SPENDS LINK BUDGET YOU MAY NOT HAVE. A 50/50 splitter
    costs about 3 dB on the through path before excess loss; the question is
    whether the production link still closes, and it is a link-budget question
    rather than a monitoring one.
  * A SNAPSHOT LENGTH IS THE LARGEST LEVER IN THE WHOLE PATH. Snapping to 128
    bytes on uniform 800-byte traffic writes about a fifth of the bytes --- and
    removes the payload that a protocol dispute would have needed.

    python3 capture_budget.py
    python3 capture_budget.py --json
    python3 test_capture_budget.py

Offline calculation in closed form. No capture was taken, no NIC was measured,
and no product's behaviour is claimed. Ring sizes, splitter losses and sustained
write rates are INPUTS to be looked up or measured on your own equipment; the
defaults here are ordinary values chosen to make the arithmetic concrete.
"""
import argparse
import json
import math
import sys

PCAP_RECORD_HEADER_BYTES = 16       # classic pcap per-packet record header
ETHERNET_OVERHEAD_BYTES = 20        # preamble, SFD and inter-frame gap


class CaptureError(ValueError):
    """Raised when a budget cannot be computed honestly from what was given."""


def _positive(name, value):
    if value is None or value <= 0:
        raise CaptureError('%s must be greater than zero' % name)
    return float(value)


def packets_per_second(link_bits_per_second, frame_bytes):
    """Frames per second at line rate, counting the inter-frame overhead."""
    link = _positive('link_bits_per_second', link_bits_per_second)
    f = _positive('frame_bytes', frame_bytes)
    if f < 64:
        raise CaptureError('an Ethernet frame is at least 64 bytes')
    return link / ((f + ETHERNET_OVERHEAD_BYTES) * 8)


def span_offer(link_bits_per_second, links_mirrored=1, directions=2,
               monitor_bits_per_second=None, utilisation=1.0):
    """What a mirror session offers its destination, against what it can take.

    The failure is not subtle and it is still routinely designed in: each
    direction of each mirrored link contributes its own traffic to a single
    output.
    """
    link = _positive('link_bits_per_second', link_bits_per_second)
    monitor = _positive('monitor_bits_per_second',
                        monitor_bits_per_second or link_bits_per_second)
    if links_mirrored < 1 or directions not in (1, 2):
        raise CaptureError('mirror at least one link, in one or two directions')
    if not 0 < utilisation <= 1:
        raise CaptureError('utilisation is a proportion above 0 and at most 1')
    offered = link * links_mirrored * directions * utilisation
    return dict(offered_bits_per_second=offered,
                monitor_bits_per_second=monitor,
                oversubscription=offered / monitor,
                fits=offered <= monitor,
                headroom_bits_per_second=monitor - offered,
                max_utilisation_that_fits=min(1.0, monitor
                                              / (link * links_mirrored
                                                 * directions)),
                note=('A mirror destination over its capacity discards, and on '
                      'most platforms it discards silently and from the COPY. '
                      'Nothing in the capture says a packet was dropped here '
                      'rather than never sent.'))


def optical_tap_budget(launch_dbm, receiver_sensitivity_dbm, fibre_loss_db,
                       connector_loss_db=1.0, monitor_split=0.30,
                       excess_loss_db=0.6):
    """Does the production link still close with a passive splitter in it?

    `monitor_split` is the fraction of optical power sent to the monitor port,
    so the through path keeps (1 - monitor_split) minus the splitter's own
    excess loss. Both paths are reported, because a tap that keeps the link up
    and starves the monitor is as useless as one that does the reverse.
    Both branches here share the supplied path loss and receiver sensitivity.
    Overload, actual branch lengths and different receivers are NOT checked;
    *_link_closes means sensitivity-only within this toy budget.
    """
    for name, v in (('fibre_loss_db', fibre_loss_db),
                    ('connector_loss_db', connector_loss_db),
                    ('excess_loss_db', excess_loss_db)):
        if v < 0:
            raise CaptureError('%s cannot be negative' % name)
    if not 0 < monitor_split < 1:
        raise CaptureError('monitor_split is a proportion strictly between '
                           '0 and 1')
    through_split_db = -10 * math.log10(1 - monitor_split)
    monitor_split_db = -10 * math.log10(monitor_split)
    fixed = fibre_loss_db + connector_loss_db
    through_rx = launch_dbm - fixed - through_split_db - excess_loss_db
    monitor_rx = launch_dbm - fixed - monitor_split_db - excess_loss_db
    without_tap = launch_dbm - fixed
    return dict(monitor_split=monitor_split,
                through_split_loss_db=through_split_db,
                monitor_split_loss_db=monitor_split_db,
                excess_loss_db=excess_loss_db,
                receive_power_without_tap_dbm=without_tap,
                through_path_receive_dbm=through_rx,
                monitor_path_receive_dbm=monitor_rx,
                margin_without_tap_db=without_tap - receiver_sensitivity_dbm,
                through_path_margin_db=through_rx - receiver_sensitivity_dbm,
                monitor_path_margin_db=monitor_rx - receiver_sensitivity_dbm,
                production_link_closes=through_rx >= receiver_sensitivity_dbm,
                monitor_link_closes=monitor_rx >= receiver_sensitivity_dbm,
                note=('Inserting a tap is a change to a production link budget '
                      'and is reviewed as one. A splitter cannot be added to a '
                      'link that was already at the edge of its margin, and '
                      'the margin is a measurement rather than a datasheet '
                      'figure.'))


def ring_drain_time(ring_descriptors, packets_per_second_in):
    """How long a NIC receive ring survives without being serviced.

    This is the time for an initially empty ring to FILL if no descriptors
    are reclaimed. Legacy drain_* names are retained for existing callers. It is unaffected by whether the
    packets arrived through a tap or a mirror.
    """
    if ring_descriptors < 1:
        raise CaptureError('a ring holds at least one descriptor')
    pps = _positive('packets_per_second_in', packets_per_second_in)
    seconds = ring_descriptors / pps
    return dict(ring_descriptors=ring_descriptors, packets_per_second=pps,
                drain_seconds=seconds, drain_microseconds=seconds * 1e6,
                note=('Loss follows if this ring remains unserviced beyond its fill time '
                      'at the stated rate and there is no other capacity. A '
                      'storage pause alone does not prove this: downstream buffers '
                      'may absorb it. Inspect NIC, driver and application counters.'))


def bytes_on_disk(link_bits_per_second, frame_bytes, snaplen=None,
                  directions=2, utilisation=1.0,
                  record_header=PCAP_RECORD_HEADER_BYTES):
    """Write rate for uniform frame lengths.

    With variable lengths, truncation needs the distribution of min(frame,snaplen),
    not min(mean(frame),snaplen). Record framing conventions are stated here.
    """
    pps = packets_per_second(link_bits_per_second, frame_bytes) * directions \
        * utilisation
    captured = frame_bytes if snaplen is None else min(frame_bytes, snaplen)
    per_packet = captured + record_header
    rate = pps * per_packet
    full = pps * (frame_bytes + record_header)
    return dict(packets_per_second=pps, captured_bytes_per_packet=captured,
                record_header_bytes=record_header,
                bytes_per_second=rate,
                gigabytes_per_second=rate / 1e9,
                terabytes_per_hour=rate * 3600 / 1e12,
                fraction_of_full_capture=rate / full if full else 0.0,
                snaplen=snaplen,
                note=('A snapshot length is the largest lever here and it is '
                      'destructive: the bytes it saves are the payload a '
                      'protocol dispute would have needed. Decide it from the '
                      'question, not from the disk.'))


def first_bottleneck(link_bits_per_second, frame_bytes, monitor_bits_per_second,
                     ring_descriptors, service_interval_seconds,
                     storage_bytes_per_second, snaplen=None, directions=2,
                     utilisation=1.0, links_mirrored=1, use_tap=False):
    """Which component discards first, given the whole path.

    Answering the chapter's own exercise: a capture design is a chain, and
    naming the weakest link is the point of budgeting it.
    """
    findings = []
    if not use_tap:
        span = span_offer(link_bits_per_second, links_mirrored, directions,
                          monitor_bits_per_second, utilisation)
        if not span['fits']:
            findings.append(dict(
                component='mirror destination',
                detail='offered %.2f Gb/s into %.2f Gb/s (%.2fx)'
                       % (span['offered_bits_per_second'] / 1e9,
                          span['monitor_bits_per_second'] / 1e9,
                          span['oversubscription'])))
    pps = packets_per_second(link_bits_per_second, frame_bytes) * directions \
        * utilisation * links_mirrored
    ring = ring_drain_time(ring_descriptors, pps)
    if service_interval_seconds > ring['drain_seconds']:
        findings.append(dict(
            component='NIC receive ring',
            detail='fills in %.0f us but is serviced every %.0f us'
                   % (ring['drain_microseconds'],
                      service_interval_seconds * 1e6)))
    disk = bytes_on_disk(link_bits_per_second, frame_bytes, snaplen, directions,
                         utilisation)
    if disk['bytes_per_second'] * links_mirrored > storage_bytes_per_second:
        findings.append(dict(
            component='storage',
            detail='needs %.2f GB/s sustained, has %.2f GB/s'
                   % (disk['bytes_per_second'] * links_mirrored / 1e9,
                      storage_bytes_per_second / 1e9)))
    return dict(observation_point='tap' if use_tap else 'mirror session',
                packets_per_second=pps, ring=ring, storage=disk,
                storage_scope="per mirrored link",
                total_storage_bytes_per_second=disk['bytes_per_second'] * links_mirrored,
                failing_components=findings,
                first_to_discard=findings[0]['component'] if findings else None,
                lossless_on_these_numbers=not findings,
                note=('"Lossless on these numbers" is a statement about the '
                      'numbers. Measure the interface, driver and application '
                      'drop counters on a real run before believing it, and '
                      'record them beside the capture.'))


def prove_every_component_can_fail():
    """FR-0052 inside the lab: each bottleneck branch must be reachable.

    A budget that can only ever blame one component is not a budget.
    """
    ten_g, frame = 10e9, 64
    cases = {
        'mirror destination': dict(use_tap=False, links_mirrored=2,
                                   ring_descriptors=1 << 20,
                                   service_interval_seconds=1e-9,
                                   storage_bytes_per_second=1e12),
        'NIC receive ring': dict(use_tap=True, ring_descriptors=4096,
                                 service_interval_seconds=1e-3,
                                 storage_bytes_per_second=1e12),
        'storage': dict(use_tap=True, ring_descriptors=1 << 20,
                        service_interval_seconds=1e-9,
                        storage_bytes_per_second=1e6),
    }
    seen = {}
    for want, kw in cases.items():
        got = first_bottleneck(ten_g, frame, 10e9, snaplen=None, **kw)
        seen[want] = got['first_to_discard']
        if got['first_to_discard'] != want:
            raise CaptureError('expected %r to fail first, got %r'
                               % (want, got['first_to_discard']))
    clean = first_bottleneck(1e9, 1500, 10e9, 1 << 20, 1e-9, 1e12, use_tap=True)
    if not clean['lossless_on_these_numbers']:
        raise CaptureError('a generously specified path still reported a '
                           'bottleneck, so the check cannot return clean')
    return dict(branches=len(cases), all_reachable=True, clean_case_reachable=True,
                routed_correctly=seen)


def _wrap(text, indent, width=78):
    words, lines, cur = text.split(), [], ''
    for word in words:
        if cur and len(cur) + len(word) + 1 > width - indent:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def report(out=None):
    out = sys.stdout if out is None else out
    proof = prove_every_component_can_fail()
    out.write('Lab 63.2 --- the capture path, budgeted end to end\n')
    out.write('=' * 74 + '\n')
    out.write('bottleneck branches proved reachable: %d, plus a clean case\n\n'
              % proof['branches'])

    out.write('WHAT A MIRROR SESSION OFFERS ITS DESTINATION\n\n')
    out.write('  %-40s %10s %8s\n' % ('configuration', 'offered', 'fits?'))
    for label, kw in (('one 10G link, one direction', dict(directions=1)),
                      ('one 10G link, both directions', dict(directions=2)),
                      ('two 10G links, both directions',
                       dict(directions=2, links_mirrored=2)),
                      ('one 10G link, both directions at 40%',
                       dict(directions=2, utilisation=0.40))):
        s = span_offer(10e9, monitor_bits_per_second=10e9, **kw)
        out.write('  %-40s %8.1f G %8s\n'
                  % (label, s['offered_bits_per_second'] / 1e9,
                     'yes' if s['fits'] else 'NO'))
    s = span_offer(10e9, directions=2, monitor_bits_per_second=10e9)
    out.write('\n  %s\n\n' % _wrap(
        'Both directions of one fully utilised link is already %.0fx the '
        'destination. It fits only while the link stays under %.0f per cent '
        'utilised in total --- which is to say it fits until the incident you '
        'bought it for. %s'
        % (s['oversubscription'], 100 * s['max_utilisation_that_fits'],
           s['note']), 2))

    out.write('AND A PASSIVE TAP SPENDS LINK BUDGET\n\n')
    out.write('  %-18s %11s %11s %10s %10s\n'
              % ('split to monitor', 'through', 'monitor', 'link up?',
                 'monitor?'))
    for split in (0.10, 0.30, 0.50, 0.70):
        b = optical_tap_budget(launch_dbm=-3.0, receiver_sensitivity_dbm=-14.4,
                               fibre_loss_db=4.0, monitor_split=split)
        out.write('  %-18s %8.2f dBm %7.2f dBm %10s %10s\n'
                  % ('%.0f%%' % (100 * split), b['through_path_receive_dbm'],
                     b['monitor_path_receive_dbm'],
                     'yes' if b['production_link_closes'] else 'NO',
                     'yes' if b['monitor_link_closes'] else 'NO'))
    b = optical_tap_budget(launch_dbm=-3.0, receiver_sensitivity_dbm=-14.4,
                           fibre_loss_db=4.0, monitor_split=0.30)
    out.write('\n  %s\n\n' % _wrap(
        'Launch -3 dBm, 4 dB of fibre, 1 dB of connectors, a receiver good to '
        '-14.4 dBm, and 0.6 dB of splitter excess loss. Without the tap the '
        'receiver sees %.2f dBm, a margin of %.2f dB. A 30 per cent tap leaves '
        'the production link %.2f dB of margin and the monitor %.2f dB. A 50 '
        'per cent tap is the one to check twice: it is the most generous to '
        'the monitor and the most expensive to the link --- and note the 10 per '
        'cent row, where the production link is comfortable and the MONITOR '
        'does not close, so the tap is installed, in the budget, and delivering '
        'nothing. %s'
        % (b['receive_power_without_tap_dbm'], b['margin_without_tap_db'],
           b['through_path_margin_db'], b['monitor_path_margin_db'],
           b['note']), 2))

    out.write('THE RING IS THE PART NOBODY BUDGETS\n\n')
    out.write('  %-30s %14s %16s\n'
              % ('frames', 'packets/s', 'ring fills in'))
    for label, frame, ring in (('64-byte frames, 4,096 ring', 64, 4096),
                               ('64-byte frames, 16,384 ring', 64, 16384),
                               ('1,500-byte frames, 4,096 ring', 1500, 4096)):
        pps = packets_per_second(10e9, frame) * 2
        r = ring_drain_time(ring, pps)
        out.write('  %-30s %14s %13.0f us\n'
                  % (label, '{:,.0f}'.format(pps), r['drain_microseconds']))
    r = ring_drain_time(4096, packets_per_second(10e9, 64) * 2)
    out.write('\n  %s\n\n' % _wrap(r['note'], 2))

    out.write('WHAT REACHES DISK, AND WHAT A SNAPSHOT SAVES\n\n')
    out.write('  %-26s %12s %14s %10s\n'
              % ('snapshot length', 'GB/s', 'TB/hour', 'of full'))
    for snap in (None, 512, 128, 64):
        d = bytes_on_disk(10e9, 800, snap, directions=2)
        out.write('  %-26s %12.3f %14.2f %9.0f%%\n'
                  % ('full frame' if snap is None else '%d bytes' % snap,
                     d['gigabytes_per_second'], d['terabytes_per_hour'],
                     100 * d['fraction_of_full_capture']))
    d = bytes_on_disk(10e9, 800, 128, directions=2)
    out.write('\n  %s\n\n' % _wrap(
        'Both directions of a 10 Gb/s link with uniform 800-byte frames. Full '
        'capture is %.2f TB an hour; snapping to 128 bytes is %.2f TB an hour, '
        'about %.0f per cent. %s'
        % (bytes_on_disk(10e9, 800, None, 2)['terabytes_per_hour'],
           d['terabytes_per_hour'], 100 * d['fraction_of_full_capture'],
           d['note']), 2))

    out.write('PUTTING THE CHAIN TOGETHER\n\n')
    for label, kw in (
            ('mirror, 2x10G both ways, 4k ring, 1 GB/s disk',
             dict(use_tap=False, links_mirrored=2, ring_descriptors=4096,
                  service_interval_seconds=200e-6,
                  storage_bytes_per_second=1e9)),
            ('tap, 1x10G both ways, 4k ring, 1 GB/s disk',
             dict(use_tap=True, ring_descriptors=4096,
                  service_interval_seconds=200e-6,
                  storage_bytes_per_second=1e9)),
            ('tap, 1x10G both ways, 64k ring, 3 GB/s disk, snap 128',
             dict(use_tap=True, ring_descriptors=65536,
                  service_interval_seconds=200e-6,
                  storage_bytes_per_second=3e9, snaplen=128))):
        r = first_bottleneck(10e9, 800, 10e9, **kw)
        out.write('  %s\n' % label)
        if r['failing_components']:
            for f in r['failing_components']:
                out.write('      %-22s %s\n' % (f['component'], f['detail']))
        else:
            out.write('      %s\n' % 'no component over budget on these numbers')
        out.write('\n')
    out.write('  %s\n' % _wrap(
        'The third row is a design rather than a hope, and it still says '
        '"on these numbers". Record the observation point and direction, the '
        'link rate, the capture filter, the snapshot length, the timestamp '
        'source and its uncertainty, the offload settings, and the interface, '
        'driver and application drop counters, beside every capture you intend '
        'to rely on.', 2))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--output')
    args = ap.parse_args(argv)
    result = dict(
        controls=prove_every_component_can_fail(),
        span={'%dx%s' % (n, d): span_offer(10e9, n, dirs, 10e9)
              for n, d, dirs in ((1, 'one-way', 1), (1, 'both', 2),
                                 (2, 'both', 2))},
        tap={('%.0f%%' % (100 * s)): optical_tap_budget(-3.0, -14.4, 4.0,
                                                       monitor_split=s)
             for s in (0.10, 0.30, 0.50)},
        ring={('%d-byte frames, %d ring' % (f, r)):
              ring_drain_time(r, packets_per_second(10e9, f) * 2)
              for f, r in ((64, 4096), (64, 16384), (1500, 4096))},
        disk={(str(s)): bytes_on_disk(10e9, 800, s, 2)
              for s in (None, 512, 128, 64)},
        chain=first_bottleneck(10e9, 800, 10e9, 4096, 200e-6, 1e9,
                               use_tap=False, links_mirrored=2))
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(json.dumps(result, indent=2) + '\n',
                                     encoding='utf8')
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        report()
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
