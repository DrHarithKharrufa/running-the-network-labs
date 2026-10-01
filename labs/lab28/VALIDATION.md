# Lab28 validation record

Completed bounded Linux execution: **20260917T024010Z**, 29 assertions passed.
The run identifier uses the isolated guest's clock; do not use it to infer
cross-host event ordering or a performance guarantee. Evidence includes the
commands/results, configuration-helper output, FRR/kernel snapshots and PCAPs.
The native archive was copied back with SHA256 equality checks and extracted
with Python's data filter. The corresponding guest job exited 0 after about
191 seconds; this is test duration, not a convergence benchmark.

Environment: isolated QEMU10.2.1 guest, Linux7.0.0-31-generic, FRR10.5.1
Ubuntu package10.5.1-1ubuntu4.1, iproute2 6.19.0. The guest has no external
network device. It uses private namespaces and a native Linux work mirror.
The host WSL kernel lacks the required SRv6 lightweight-tunnel capability.
Extracted tools/kernel do not install or repair the host's package database.

## Executed

- IPv6 IS-IS locator reachability after convergence; no customer service before
  the static SRv6 mapping; exact delivered configure-srv6.py on all four routers.
- End, End.X and blue/red End.DT4 service forwarding, with overlapping tenant
  IPv4 addresses and both return directions.
- Missing blue service SID loses blue delivery while red remains usable;
  reinstating the correct table restores blue.
- seg6_enabled=0 on the tested ingress interface does not disable the explicit
  seg6local End entry. Removing the actual entry loses that addressed service.
  A list bypassing the instruction still uses that router as IPv6 transit;
  restoring the entry/list recovers the original path.
- Full three-SID, reduced three-SID and reduced one-SID delivery. Independent
  raw-byte analysis checks eight captures/24 packets: full overhead96 bytes,
  reduced three-SID80, reduced one-SID40. Full Segments Left progresses2/1/0.
- Correct blue mapping delivers only at the selected right-hand attachment.
  A deliberately wrong red service SID delivers requests into red although
  the ping fails with return mapping to the other customer. Capture, not ping
  failure alone, reveals the isolation defect. Mapping correction restores it.
- MTU2000 carries a1500-byte inner IPv4 packet. With both first-link ends at
  MTU1500, inner1404 succeeds and1405 fails for the full three-SID96-byte
  header. Restoring2000 restores1500-byte inner delivery.
- NEXT-CSID64/16 with two shifting End instructions and terminal End.DT4:
  one three-instruction destination container, no SRH,40-byte overhead.
  Independent capture decoding verifies all three successive destinations.
  Restoration to the ordinary three-SID list succeeds.

The arithmetic/bit model separately has27 passing cases in
work/publication/full-review/srv6-arithmetic-check.json. A model does not
verify hardware slot capacity, interoperability or throughput.

## Failed and incomplete attempts retained

- 20260917T014433Z: startup timeout, no protocol assertion passed.
- 20260917T014723Z: nine assertions passed before the incorrect expectation
  that the interface SR knob blocks an explicit endpoint failed. The observed
  behaviour is retained as a boundary warning, not concealed as a passing test.
- 20260917T015138Z:22 assertions printed, then a600-second timeout while copying
  observations; partial files, no final results.json. It is not a completed run.
- Subsequent Windows-share attempt timed out at startup without assertions.
  WSL then failed to start twice (0x800705b4). A graceful subsystem restart and
  private native workspace allowed the completed run above. This does not
  establish a general cause for every filesystem or WSL performance problem.

## Not executed

Docker build, Containerlab adapter/start scripts, commercial NOS/ASIC/controller,
BGP SRv6 service signalling, IPv6 customer payload/DT6/DT46, L2 behaviours,
proxy chaining, REPLACE-CSID, every block size or mixed-format profile,
hardware rate/scale, protected End.X link failure, full PMTUD/UDP/TCP suite,
and an unauthorised-ingress ACL test. These need their own acceptance records.
The exact static helper is executed; the Docker wrapper is not.
