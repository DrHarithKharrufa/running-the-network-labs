# Lab 59.1–59.3 — candidates, coverage, and what a detection is worth

```bash
python3 flow_hunt.py            # candidates from flow data, with what they still need
python3 telemetry_limits.py     # what your telemetry could possibly have seen
python3 detector_quality.py     # jitter, base rates, and the two costs
python3 test_flow_hunt.py          # 49 checks
python3 test_telemetry_limits.py   # 42 checks
python3 test_detector_quality.py   # 42 checks
```

All three are offline calculation over synthetic data with a fixed seed. Nothing
here touches a network, a product or a real capture.

## 59.1 — the hunt that called group policy an attack

The version that shipped declared an intrusion from nine synthetic records. Four
separate things were wrong with how it did it:

| the defect | why it matters |
|---|---|
| `("workstation", 445)` listed as forbidden | **every domain-joined workstation** reaches the DC on SMB, continuously, for SYSVOL and NETLOGON. The first alert is every laptop in the building |
| `d.startswith(("dc","app","ws"))` decided what was external | a host called `dc.attacker.example` is internal; any internal host outside the naming convention is the Internet |
| largest outbound flow printed as "exfil staging" | a backup, an update, a video call and a database replica are all larger than most attacks |
| `min()` called the first record the incident start | and raised `ValueError` for a host with no flows, so asking about a quiet host crashed the tool |

The rebuilt version classifies by **address** against an inventory, and judges
internal traffic against an **expected-service list** that states its reasons —
the artefact a blocklist quietly assumes exists. Workstation SMB to the domain
controller comes back `EXPECTED`, with the reason. Workstation RDP to a domain
controller comes back `CANDIDATE`, and the sentence attached is *"nobody wrote
this down"*, not *"this should not happen"* — because plenty of legitimate
administration is undocumented, and the first useful output of the rule is
usually a better list.

Periodicity is reported as a **number**, with the warning that legitimate
software produces the same number. Scoping returns its own limits: first-observed
is the first record *in this window* (and the model says when that is the window
edge), the largest flow is the largest flow, and a host with no records returns
cleanly with *"that is not evidence the host was quiet"*.

## 59.2 — what could possibly have been seen

At 1:2048 packet sampling:

```
  connection                                           P(sampled)  byte est.
  a DNS query and response (4 packets)                    0.0020    +-2262%
  a short TLS handshake and one request (20 packets)      0.0097    +-1012%
  an interactive SSH session (500 packets)                0.2167     +-202%
  a 100 MB download (70,000 packets)                      1.0000      +-17%
```

A DNS lookup has about **two chances in a thousand** of appearing. An
investigator who concludes "this host never resolved that name" from an empty
query is reading the sampling rate.

Chain the three independent failures and a beacon check-in on a partially
covered path has a **0.3 %** chance of leaving a trace. Traffic between two
machines that never crosses an exporter has none at all, however good the rest of
the pipeline is.

And capture is a window, not a record: **1 TB at 5 Gb/s is under 27 minutes**. A
128-byte snaplen stretches it to about three hours, at the price of the payload
you were capturing for.

## 59.3 — what a detection is worth

A periodicity detector, swept against jitter, beside real-shaped benign traffic:

```
    hourly cron job              CV 0.000
    telemetry push every 60s     CV 0.026
    a person browsing            CV 0.906

  jitter           CV  detected?
  +-0%          0.000        yes
  +-20%         0.106        yes
  +-30%         0.162         NO
```

The beacon the detector just missed scores **0.162**. The cron job scores
**0.000**. To catch the beacon the threshold must be loosened past the cron job
and the telemetry push. **There is no threshold that catches a jittered beacon
and leaves the scheduled jobs alone.**

Then the base rate. The same rule, the same data, two months:

```
  50 compromised of 100,000        precise tuning: 75.0% precise, misses 35 of 50
   2 compromised of 100,000        precise tuning: 10.7% precise, misses 1.4 of 2
```

Precision is not a property of a rule. Tuning on the false-positive queue alone
always converges on a quiet queue and an undetected intrusion.

## What to take away

- Absence of a record is not absence of a connection — compute how absent it
  would have been anyway.
- A rate or a byte count from sampled telemetry is an estimate. Rank with it;
  do not quote it.
- An internal connection is suspicious only against a written statement of what
  is expected.
- Price both costs of a detection. The queue is visible and the misses are not.
