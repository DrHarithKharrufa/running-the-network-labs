# Changelog

Editions of the companion, newest first. A tagged release is frozen; this file
in the repository's current state records what moved between tags. Corrections
made after an edition was printed go in `ERRATA.md`.

## RTN-2026-10-04

The workbook's first page. RTN-2026-10-03 is unchanged and stays available
under its own tag.

- **The Configuration Workbook now opens with the cover design.** Its first page
  was still the earlier title page with a drawn network diagram. It now uses the
  same print-resolution illustration and type as the book's cover and the colour
  edition's first page, under the workbook's own title, so the two volumes read
  as a pair and cannot be mistaken for each other. The picture is placed at about
  319 ppi. The workbook keeps its 528 pages; no task, panel or evidence mark
  changed.
- **The identifier is RTN-2026-10-04 although the edition was built and published
  on 3 October 2026.** RTN-2026-10-03 had already been published that day, and a
  published tag is never changed; `EDITION.json` says so in `identifier_note`.
- The book, workbook, cover and companion carry the new identifier and
  `EDITION.json` records the SHA-256 of the new PDFs. In the book, only the
  companion page (page xii) changed in content. The cover is byte-identical to
  RTN-2026-10-03's. The companion's labs, programs and evidence are byte-identical
  to RTN-2026-10-03; the learning guides and `prerequisites.json` change only in
  their edition line.
- This edition's test run is `test-results-2026-10-03/execution-RTN-2026-10-04.json`.
  The earlier run of the same day, made for RTN-2026-10-03, stays beside it as
  `execution.json`.

## RTN-2026-10-03

The print-resolution cover. RTN-2026-10-02 is unchanged and stays available
under its own tag.

- **The cover illustration is now above 300 ppi wherever it is printed.** The
  approved image was 1054 × 1492 pixels, about 126 ppi across the printed front
  cover and 161 ppi on the book's title page. It was enlarged with the Real-ESRGAN
  x4plus super-resolution model and resampled to 2635 × 3730 pixels — exactly
  2.5 times the original, so the composition, framing and colours are unchanged —
  giving about 314 ppi on the cover, 403 ppi on the print title page and 319 ppi
  on the colour edition's first page.
- The book, workbook, cover and companion carry the new identifier and
  `EDITION.json` records the SHA-256 of the new PDFs. The companion's labs,
  programs and evidence are byte-identical to RTN-2026-10-02; the learning
  guides and `prerequisites.json` change only in their edition line.
- This edition's test run is recorded in `test-results-2026-10-03/`.

## RTN-2026-10-02

The reader edition of the book, with the 120-task Configuration Workbook and
everything it uses now public. RTN-2026-10-01 is unchanged and stays available
under its own tag.

- **The book is 87 chapters and 714 print pages** (750 before). Four former
  chapters now share a chapter with a neighbour; every subject, section and all
  500 exercises remain, and the worked answers follow the new numbering. Most of
  the saving is layout: page geometry, chapter heads, part openings and a
  contents list of chapters only, with body and code sizes unchanged.
- **Reading pauses.** Fifty-one editorial cartoons, twelve two-minute mysteries
  with their reveals in the book's Appendix H, ten workplace scenes and twelve
  service checkpoints that follow one fictional WAN trial. Markdown copies are in
  `learning/creative-reading/`. None of them adds a laboratory result.
- **Lab numbers are stable identifiers.** Lab directories keep their original
  numbers, so `labs/lab64` belongs to Chapter 63. `INDEX.md` gives the printed
  chapter, `learning/CHAPTER-MAP.md` converts both ways, and
  `check-environment.py` takes `--lab-id` (`--chapter` remains as an alias).
  Program banners written for the earlier numbering are left as they were, so the
  recorded hashes of those programs stay valid.
- **The Configuration Workbook's helpers.** `workbook-automation/` (an offline
  kit: 196 guard/XML checks and 21 counter checks, `device_execution=false`),
  `workbook-fixtures/` (preparation contracts), `TASK-NAVIGATOR.md`,
  `READER-MAP.json`, and `workbook-baselines/documented-sources.json`, which now
  holds every READ source for all 120 tasks — 714 READ and six NO_PANEL vendor
  outcomes, each READ entry with its official URL, version and retrieval date.
  READ is documentary syntax evidence, not a device run.
- **Corrections.** `prerequisites.json` now declares Jinja2 for Lab69's test
  program, which failed on a clean machine under the previous edition's runner.
  `labs/lab53/urpf_modes.py` describes three namespaces, which is what it builds,
  not four, and the Lab53 README no longer presents feasible-path uRPF as an
  ownership check. `labs/reference-designs/BRANCH-COMPLETE.md` tightens source
  validation (IPv6 link-local, spoofed sources, non-IP frames), DHCP lease state
  in the degraded path, the spanning-tree roles and costs, the CPE transit profile
  and the budget definition, while its generated addressing block and both checkers
  still pass. The Lab64 README states the assumptions behind its posterior figures.
- **Evidence.** This edition's run passes all 109 declared test programs on one
  Linux host, including both privileged Lab53 suites (`test-results-2026-10-02/`).
  `evidence/review-2026-10-01-codex/` keeps the independent review's own runs.
- **Line endings.** Every text file in the release is LF again. Some files had
  been written with CRLF during the review, which would have made
  `SHA256SUMS.txt` disagree with a checkout of this tag.

## RTN-2026-10-01

Corrections from a third independent reader and publication review. The theme of
this round is that several earlier repairs named a mechanism without establishing
that it delivered the promised result.

- **The reader's first five minutes now work as printed.** The book's retrieval
  page ended by putting you in the repository root and then told you to `cd` into
  a second copy of the repository beneath it. Both download routes now declare
  one starting directory — the folder holding `EDITION.json` — and every command
  is relative to it. The git example no longer uses a Unix backslash continuation
  in a page that advertises a Windows workflow, and the failure guidance no longer
  says a failure means "the problem is Python": it lists the three errors you
  actually get, and only one of them is Python.
- **One authority for the edition identity.** Eleven reader-facing files repeated
  the edition in their own words, and this download previously introduced itself
  as RTN-2026-09-26 "matching the 746-page print proof" while the book's own page
  said RTN-2026-09-27 and 748 pages. `EDITION.json` is now the only authority and
  `tools/stamp_edition.py` stamps and then polices every other mention; an
  undeclared stale identifier anywhere in the payload fails the check.
  `QUALIFICATION.md` now says plainly which of its runs belong to this edition and
  which are carried forward with their original dates.
- **`labs/reference-designs/BRANCH-COMPLETE.md`: three mechanisms specified
  rather than asserted.**
  - Controller isolation no longer rests on protected ports, which are local to
    one switch: with two switches joined by a trunk, a protected port still
    forwards to the trunk and the far switch still delivers to its protected
    port. The control is now an ingress filter on every controller port on both
    switches, the port map places a controller on each switch deliberately, and
    the acceptance test covers the same-switch *and* cross-switch cases.
  - Voice continuity across a WAN change no longer rests on a loopback-sourced
    tunnel. A loopback keeps the inner addresses stable; it does nothing for the
    outer endpoint or its NAT mapping. The design now runs two IKEv2 tunnels, one
    per WAN, and names IKEv2 MOBIKE as the single-tunnel alternative with the
    condition RFC 4555 actually places on it.
  - The router-failure procedure is specified end to end: the switch port's
    degraded profile, the CPE's prepared gateway and DHCP scope, who can apply
    the change and over what path, which services survive and which do not, and
    two separately measured deadlines instead of a shipping promise standing in
    for a restoration target.
  - R-01 covers link *and access-switch* failure again. Narrowing it to links in
    the previous round silently dropped a commitment that D-03, FT-04 and RP-02
    all still depended on.
- **`check_addressing.py` now matches what it claims.** It validates the assigned
  device loopbacks, not only their pools, and the addressing block in the document
  is *generated* from the JSON and compared byte for byte, so a changed DHCP
  endpoint, loopback or spare block in the prose fails the check. It previously
  reported that "the document agrees with the source" while comparing only the LAN
  prefixes. `test_check_addressing.py` is new and keeps fifteen bad-input cases,
  including the three the reviewer used.
- **The incident record stops claiming a clock bound it cannot support.** The
  model answer previously derived ±20 ms from a pre-incident offset reading and a
  dispersion figure, which do not combine into a bound and which exceed 20 ms
  anyway. It now says so, shows that the ordering the record relies on is 81
  seconds and survives without a bound, and gives the three terms a real bound
  needs.
- **Three new FRR 10.2.1 runs settle the workbook's OSPF Init explanation**, in
  `evidence/revision-2026-10-01/`. The same mask mismatch on the same pair of
  routers is harmless on a point-to-point link, fatal at both ends on a broadcast
  link, and produces a persistent Init on exactly one side when the interface
  types differ. The workbook now says *persistently* stuck in Init, and says the
  receive checks that apply to the interface type rather than listing the mask
  unconditionally.
- Smaller corrections: the ADR's requirement count and alternative rows name the
  requirements instead of saying "both"; the guest ACL names its direction; the
  workbook PDF no longer carries the LaTeX and pdfTeX banner; `--case` lets a
  reader put an incident through lab 64.2 without editing the program; the
  inventory count now sums every dated evidence revision rather than one
  hard-coded folder.

## RTN-2026-09-27

Corrections from a second independent reader and publication review.

- `labs/reference-designs/BRANCH-COMPLETE.md` rebuilt. The address plan moves to
  `10.10.64.0/22` and `2001:db8:a1de:300::/56`, from the space Appendix C leaves
  unallocated rather than from London's growth reservation. The IPv6 site prefix
  is now canonical — the previous `2001:db8:a1de:18::/56` had host bits set and
  did not contain its own LANs. The "spare" IPv4 block is genuinely spare; the
  previous one sat inside the guest subnet. Loopbacks move to their own pool.
- `labs/reference-designs/branch-hgt.json` is now the single source for those
  allocations, and `check_addressing.py` validates it and checks the printed
  table still matches.
- The same design gained a requirement exception (R-01a) rather than accepting a
  failure against R-01, a forwarding device for the router-failure fallback,
  a stated voice-continuity mechanism, intra-VLAN isolation and an IPv6 policy
  for the building systems, a failback hold-down, a port map, and a bill of
  materials with quantity, unit price and extended total stated separately.
- `learning/ASSESSING-YOUR-ANSWER.md`: the capacity standard is rebuilt from
  Chapter 67's exercise as printed — six months of delivery time, not four — and
  the added-conditions version is separated out and made internally consistent.
  The architecture decision now rejects its alternative against the requirement
  that actually excludes it. The incident record distinguishes a clock offset
  from an uncertainty bound. Several rubric absolutes are softened to match what
  the book teaches about bounded evidence.
- Lab introductions for 42, 44, 53, 62 and 64 present their flawed comparisons
  as counterexamples rather than as the author's earlier drafts.

## RTN-2026-09-26

First public release. 84 laboratory exercises, 252 Python programs, 35
Containerlab topologies, the execution harness and the eight-session graded
practical route.

Note on the tag: an earlier `RTN-2026-09-26` tag was published, then deleted and
recut against the final build because the page count changed after it was cut
and its recorded PDF hashes no longer matched. If you hold a copy fetched
between those two points, `EDITION.json` will disagree with your PDFs; fetch the
release again. A tag should not be recut, which is why this edition takes a new
identifier instead.
