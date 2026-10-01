#!/usr/bin/env python3
"""Lab 63.3 --- what a log transport guarantees, and what it costs to buffer.

Chapter 63 says reliable transport is not the same as durable, searchable
storage. That is right, and it is usually where the discussion stops. This lab
takes it further, because every one of the following is a number somebody has to
choose and almost nobody computes:

  * WHAT EACH HOP ACTUALLY PROMISES. TCP promises ordered delivery to a socket
    while the connection lasts. A relay that has acknowledged a socket write and
    holds the event in memory has promised nothing about a restart, and nothing
    in the sender's logs will say so.
  * WHAT A BUFFER SURVIVES. At 8,000 events a second, a fifteen-minute sink
    outage is 7.2 million events. At 400 bytes each that is 2.88 GB of disk, and
    a default relay queue is measured in tens of megabytes.
  * WHAT CATCHING UP COSTS. A fifteen-minute outage drained by a sink with 2,000
    events a second of spare capacity takes an HOUR, during which every search
    is answering from incomplete data without saying so.
  * WHAT KAFKA DOES AND DOES NOT ADD. Replication is durability only at the
    acknowledgement setting that waits for it, and only with unclean leader
    election disabled.

    python3 log_delivery.py
    python3 log_delivery.py --json
    python3 test_log_delivery.py

Offline calculation in closed form. No pipeline was run, no broker was started,
and no product's behaviour is claimed: the guarantee table below is a statement
about protocol and configuration semantics, and your own stack's settings are
the authority for your own stack.
"""
import argparse
import json
import sys

# What each hop guarantees, and --- the column that matters --- what it does not.
TRANSPORTS = {
    'syslog over UDP': dict(
        ordered=False, delivery_acknowledged=False, receiver_process_receipt=False,
        durable_commit=False, replicated=False, detects_loss=False,
        does_not=('The sender cannot tell a delivered datagram from a dropped '
                  'one. Loss is silent at both ends and there is no sequence '
                  'number to notice a gap with unless the application added '
                  'one.')),
    'syslog over TCP': dict(
        ordered=True, delivery_acknowledged=True, receiver_process_receipt=False,
        durable_commit=False, replicated=False, detects_loss=True,
        does_not=('TCP acknowledges bytes reaching the receiver kernel. It says '
                  'nothing about the receiving process having read them, still '
                  'less about storage. Events in a socket buffer at the moment '
                  'of a restart are gone, acknowledged.')),
    'syslog over TLS/TCP': dict(
        ordered=True, delivery_acknowledged=True, receiver_process_receipt=False,
        durable_commit=False, replicated=False, detects_loss=True,
        does_not=('TLS adds confidentiality and peer authentication when it is '
                  'configured to verify. It adds nothing to durability, and a '
                  'certificate that expires turns a working pipeline into a '
                  'silent one.')),
    'relay with disk queue': dict(
        ordered=True, delivery_acknowledged=True, receiver_process_receipt=True,
        durable_commit=True, replicated=False, detects_loss=True,
        does_not=('The queue is durable on ONE host. It survives a sink outage '
                  'and a relay restart; it does not survive the relay\'s disk, '
                  'and its capacity is a number you must size against the '
                  'outage you intend to survive.')),
    'Kafka, acks=0': dict(
        ordered=True, delivery_acknowledged=False, receiver_process_receipt=False,
        durable_commit=False, replicated=False, detects_loss=False,
        does_not=('Fire and forget with extra steps. The producer does not wait '
                  'for the broker at all, so this is UDP semantics over a '
                  'durable log.')),
    'Kafka, acks=1': dict(
        ordered=True, delivery_acknowledged=True, receiver_process_receipt=True,
        durable_commit=True, replicated=False, detects_loss=True,
        does_not=('The leader acknowledged; the followers may not have copied '
                  'it. Losing the leader before replication can lose an acknowledged '
                  'write; loss is possible, not guaranteed on every failure.')),
    'Kafka, acks=all, min.insync=2 of 3': dict(
        ordered=True, delivery_acknowledged=True, receiver_process_receipt=True,
        durable_commit=True, replicated=True, detects_loss=True,
        does_not=('Survives one broker. It does not survive unclean leader '
                  'election, which can elect a replica that never had the '
                  'write, nor a consumer that commits its offset before doing '
                  'the work, nor a retention window shorter than the outage you '
                  'are recovering from.')),
}

PROPERTIES = ('ordered', 'delivery_acknowledged', 'receiver_process_receipt',
              'durable_commit', 'replicated', 'detects_loss')


class DeliveryError(ValueError):
    """Raised when a pipeline question cannot be answered from what was given."""


def transport(kind):
    if kind not in TRANSPORTS:
        raise DeliveryError('unknown transport %r; known: %s'
                            % (kind, ', '.join(sorted(TRANSPORTS))))
    return dict(TRANSPORTS[kind], name=kind)


def buffer_survival(events_per_second, buffer_events, outage_seconds):
    """Does the buffer hold through the outage, and what is lost if not."""
    for name, v in (('events_per_second', events_per_second),
                    ('buffer_events', buffer_events),
                    ('outage_seconds', outage_seconds)):
        if v < 0:
            raise DeliveryError('%s cannot be negative' % name)
    arriving = events_per_second * outage_seconds
    overflow = max(0.0, arriving - buffer_events)
    return dict(events_per_second=events_per_second,
                buffer_events=buffer_events, outage_seconds=outage_seconds,
                events_arriving_during_outage=arriving,
                holds=overflow == 0,
                events_lost=overflow,
                seconds_of_headroom=(buffer_events / events_per_second
                                     if events_per_second else float('inf')),
                note=('An overflowing queue discards, and which end it discards '
                      'from is a configuration choice with consequences: '
                      'dropping the newest loses the incident you are in, '
                      'dropping the oldest loses how it started.'))


def buffer_sizing(events_per_second, outage_seconds, bytes_per_event=400):
    """The buffer an intended survivable outage actually requires."""
    for name, v in (('events_per_second', events_per_second),
                    ('outage_seconds', outage_seconds),
                    ('bytes_per_event', bytes_per_event)):
        if v <= 0:
            raise DeliveryError('%s must be greater than zero' % name)
    events = events_per_second * outage_seconds
    return dict(events_required=events,
                bytes_required=events * bytes_per_event,
                gigabytes_required=events * bytes_per_event / 1e9,
                note=('Size the queue against the outage you intend to survive '
                      'and state that intention, because the default is sized '
                      'against nothing in particular.'))


def drain_time(events_per_second_in, sink_events_per_second, queued_events):
    """How long the backlog takes to clear, while new events keep arriving.

    The number people expect is queue divided by sink rate. The number they get
    is queue divided by the SURPLUS, and if there is no surplus the backlog
    never clears at all.
    """
    if events_per_second_in < 0 or sink_events_per_second <= 0:
        raise DeliveryError('input cannot be negative and the sink must accept '
                            'something')
    if queued_events < 0:
        raise DeliveryError('a backlog cannot be negative')
    surplus = sink_events_per_second - events_per_second_in
    if surplus <= 0:
        return dict(surplus_events_per_second=surplus, drains=False,
                    seconds_to_drain=None,
                    naive_seconds=queued_events / sink_events_per_second,
                    note=('The sink is not faster than the source, so the '
                          'backlog never clears and the lag grows without '
                          'bound. This is a capacity fault, not a slow '
                          'recovery.'))
    seconds = queued_events / surplus
    return dict(surplus_events_per_second=surplus, drains=True,
                seconds_to_drain=seconds, minutes_to_drain=seconds / 60.0,
                naive_seconds=queued_events / sink_events_per_second,
                optimism_factor=(seconds
                                 / (queued_events / sink_events_per_second)),
                note=('Until it drains, every search is answering from '
                      'incomplete data. Say so on the dashboard, or somebody '
                      'will conclude an event did not happen.'))


def kafka_durability(acks, replicas, min_insync, unclean_leader_election=False,
                     brokers_lost=1):
    """Lower-bound acknowledgement model, not per-record disk-flush simulation.

    survives=False means survival is not guaranteed by these settings, not
    that every such failure necessarily loses a record. replicas describes
    configured replication; min_insync is a lower bound on copies for an
    accepted acks=all write. No per-record fsync or complete power-loss model.
    """
    if acks not in (0, 1, 'all'):
        raise DeliveryError("acks is 0, 1 or 'all'")
    if replicas < 1 or min_insync < 1:
        raise DeliveryError('replicas and min.insync.replicas are at least 1')
    if min_insync > replicas:
        raise DeliveryError('min.insync.replicas cannot exceed the replica '
                            'count; the topic will refuse writes')
    if brokers_lost < 0:
        raise DeliveryError('brokers_lost cannot be negative')
    copies_on_ack = (0 if acks == 0 else 1 if acks == 1 else min_insync)
    survives = copies_on_ack - brokers_lost >= 1
    reasons = []
    if acks == 0:
        reasons.append('the producer never waited for the broker')
    elif acks == 1:
        reasons.append('only the leader copy is required at acknowledgement; more may exist')
    else:
        reasons.append('at least %d in-sync copies were required for an accepted write'
                       % min_insync)
    if unclean_leader_election and survives:
        survives = False
        reasons.append('unclean leader election can promote a replica that '
                       'never received the write, which discards it after '
                       
                       'acknowledgement.')
    return dict(acks=acks, replicas=replicas, min_insync=min_insync,
                unclean_leader_election=unclean_leader_election,
                brokers_lost=brokers_lost,
                copies_at_acknowledgement=copies_on_ack,
                survives=survives, reasons=reasons,
                note=('Replication is durability only at the acknowledgement '
                      'setting that waits for it. And none of this addresses '
                      'retention: a topic that ages records out faster than '
                      'you recover from a backlog loses them to policy rather '
                      'than to failure.'))


def accounting(generated, received, persisted, searchable):
    """The four counts the chapter's own outage test asks you to compare.

    Each gap has a different cause and a different fix, and a pipeline
    instrumented only at the socket sees none of them.
    """
    counts = dict(generated=generated, received=received, persisted=persisted,
                  searchable=searchable)
    for name, v in counts.items():
        if v < 0:
            raise DeliveryError('%s cannot be negative' % name)
    if not generated >= received >= persisted >= searchable:
        raise DeliveryError('the counts must be non-increasing along the '
                            'pipeline (%s); if they are not, something is '
                            'duplicating and that is the finding'
                            % ', '.join('%s=%d' % kv for kv in counts.items()))
    gaps = [
        dict(stage='generated to received', lost=generated - received,
             means='transport or sender-side loss: UDP drops, a dead '
                   'connection, a rate limit, or a source that stopped'),
        dict(stage='received to persisted', lost=received - persisted,
             means='the receiver had it and did not keep it: a full queue, a '
                   'parse failure routed to nowhere, or a restart with events '
                   'in memory'),
        dict(stage='persisted to searchable', lost=persisted - searchable,
             means='it is on disk and the index does not know: indexing '
                   'backlog, a mapping rejection, or a retention rule that '
                   'already removed it'),
    ]
    return dict(counts=counts, gaps=gaps,
                total_lost=generated - searchable,
                end_to_end_fraction=(searchable / float(generated)
                                     if generated else 0.0),
                note=('Measure all four with numbered synthetic events during '
                      'a deliberate outage. A pipeline that reports only '
                      '"delivered" is reporting the one number that cannot '
                      'distinguish these.'))


def prove_the_distinctions_bite():
    """FR-0052 inside the lab: each guarantee and each branch must separate.

    A table where every transport has the same properties teaches nothing, and
    a drain calculation that always drains would hide the case that matters.
    """
    for prop in PROPERTIES:
        values = {t[prop] for t in TRANSPORTS.values()}
        if len(values) < 2:
            raise DeliveryError('every transport agrees on %r, so the column '
                                'distinguishes nothing' % prop)
    if transport('syslog over TCP')['durable_commit']:
        raise DeliveryError('TCP is being credited with durability')
    if not transport('relay with disk queue')['durable_commit']:
        raise DeliveryError('a disk queue is not being credited with durability')
    if transport('Kafka, acks=1')['replicated']:
        raise DeliveryError('acks=1 is being credited with replication')
    if not kafka_durability('all', 3, 2)['survives']:
        raise DeliveryError('acks=all with two in-sync copies should survive '
                            'one broker')
    if kafka_durability(1, 3, 2)['survives']:
        raise DeliveryError('acks=1 alone should not guarantee survival after losing the leader')
    if kafka_durability('all', 3, 2, unclean_leader_election=True)['survives']:
        raise DeliveryError('unclean leader election should defeat acks=all')
    if drain_time(8000, 7000, 1000)['drains']:
        raise DeliveryError('a sink slower than the source should never drain')
    if not drain_time(8000, 10000, 1000)['drains']:
        raise DeliveryError('a sink faster than the source should drain')
    if buffer_survival(8000, 1_000_000, 900)['holds']:
        raise DeliveryError('a one-million-event queue should not hold fifteen '
                            'minutes at 8,000 events a second')
    return dict(all_columns_discriminate=True, tcp_not_durable=True,
                disk_queue_durable=True, acks1_not_replicated=True,
                acks_all_survives_one_broker=True,
                unclean_election_defeats_it=True,
                slow_sink_never_drains=True, fast_sink_drains=True,
                undersized_queue_overflows=True)


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
    proof = prove_the_distinctions_bite()
    out.write('Lab 63.3 --- what a log transport guarantees, and what buffering costs\n')
    out.write('=' * 74 + '\n')
    out.write('controls: %d properties, all of which separate the transports\n\n'
              % len(PROPERTIES))

    out.write('WHAT EACH HOP PROMISES\n\n')
    head = ('ord', 'ack', 'proc', 'dur', 'repl', 'sees loss')
    out.write('  %-36s %s\n' % ('', ' '.join('%-5s' % h for h in head)))
    for name in ('syslog over UDP', 'syslog over TCP', 'syslog over TLS/TCP',
                 'relay with disk queue', 'Kafka, acks=0', 'Kafka, acks=1',
                 'Kafka, acks=all, min.insync=2 of 3'):
        t = transport(name)
        out.write('  %-36s %s\n'
                  % (name, ' '.join('%-5s' % ('yes' if t[p] else '-')
                                    for p in PROPERTIES)))
    out.write('\n  %s\n\n' % _wrap(
        'ord=ordered, ack=delivery acknowledged, proc=the receiving PROCESS had '
        'it, dur=committed to durable storage, repl=replicated beyond one host. '
        'The two columns that get conflated are ack and dur, and the gap between '
        'them is where a pipeline loses events while reporting success: '
        + transport('syslog over TCP')['does_not'], 2))

    out.write('WHAT A BUFFER SURVIVES, AT 8,000 EVENTS A SECOND\n\n')
    out.write('  %-26s %14s %12s %14s\n'
              % ('queue size', 'headroom', 'holds 15 min?', 'events lost'))
    for label, q in (('50,000 events', 50_000),
                     ('1,000,000 events', 1_000_000),
                     ('7,200,000 events', 7_200_000)):
        b = buffer_survival(8000, q, 900)
        out.write('  %-26s %11.0f s %12s %14s\n'
                  % (label, b['seconds_of_headroom'],
                     'yes' if b['holds'] else 'NO',
                     '{:,.0f}'.format(b['events_lost'])))
    z = buffer_sizing(8000, 900)
    out.write('\n  %s\n\n' % _wrap(
        'To survive fifteen minutes at that rate you need %s events of queue, '
        'which at 400 bytes each is %.2f GB of disk. %s'
        % ('{:,.0f}'.format(z['events_required']), z['gigabytes_required'],
           z['note']), 2))

    out.write('AND WHAT CATCHING UP COSTS\n\n')
    out.write('  %-30s %12s %14s %12s\n'
              % ('sink capacity', 'surplus/s', 'time to drain', 'naive guess'))
    for sink in (7_500, 8_500, 10_000, 16_000):
        d = drain_time(8000, sink, 7_200_000)
        out.write('  %-30s %12s %14s %10.0f s\n'
                  % ('%s events/s' % '{:,}'.format(sink),
                     '{:,}'.format(int(d['surplus_events_per_second'])),
                     ('never' if not d['drains']
                      else '%.0f min' % d['minutes_to_drain']),
                     d['naive_seconds']))
    d = drain_time(8000, 10_000, 7_200_000)
    out.write('\n  %s\n\n' % _wrap(
        'A fifteen-minute outage with 2,000 events a second of spare sink '
        'capacity takes %.0f minutes to clear, not the %.0f minutes that '
        'dividing the backlog by the sink rate suggests --- an optimism factor '
        'of %.1f. %s'
        % (d['minutes_to_drain'], d['naive_seconds'] / 60.0,
           d['optimism_factor'], d['note']), 2))

    out.write('WHAT REPLICATION ADDS, AND ONLY AT THE RIGHT SETTING\n\n')
    out.write('  %-40s %10s %s\n' % ('configuration', 'survives', 'because'))
    for label, args in (
            ('acks=0', (0, 3, 2)),
            ('acks=1', (1, 3, 2)),
            ('acks=all, min.insync=1 of 3', ('all', 3, 1)),
            ('acks=all, min.insync=2 of 3', ('all', 3, 2))):
        k = kafka_durability(*args)
        out.write('  %-40s %10s %s\n'
                  % (label, 'yes' if k['survives'] else 'NO',
                     _wrap(k['reasons'][0], 53)))
    u = kafka_durability('all', 3, 2, unclean_leader_election=True)
    out.write('\n  %s\n\n' % _wrap(
        'Losing one broker. And the last row above stops surviving the moment '
        'unclean leader election is enabled: ' + u['reasons'][-1] + ' ' + u['note'], 2))

    out.write('THE FOUR COUNTS TO COMPARE DURING A DELIBERATE OUTAGE\n\n')
    a = accounting(1_000_000, 994_000, 961_000, 947_000)
    for g in a['gaps']:
        out.write('  %-26s %10s  %s\n'
                  % (g['stage'], '{:,}'.format(g['lost']), _wrap(g['means'], 40)))
    out.write('\n  %s\n' % _wrap(
        'End to end, %.1f per cent of the events are searchable, and the three '
        'gaps have three different owners. %s'
        % (100 * a['end_to_end_fraction'], a['note']), 2))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--output')
    args = ap.parse_args(argv)
    result = dict(
        controls=prove_the_distinctions_bite(),
        transports={k: transport(k) for k in sorted(TRANSPORTS)},
        buffer={('%d events' % q): buffer_survival(8000, q, 900)
                for q in (50_000, 1_000_000, 7_200_000)},
        sizing=buffer_sizing(8000, 900),
        drain={('sink %d' % s): drain_time(8000, s, 7_200_000)
               for s in (7_500, 8_500, 10_000, 16_000)},
        kafka={'acks=%s,min=%d' % (a, m): kafka_durability(a, 3, m)
               for a, m in ((0, 2), (1, 2), ('all', 1), ('all', 2))},
        accounting=accounting(1_000_000, 994_000, 961_000, 947_000))
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
