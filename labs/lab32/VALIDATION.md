# Lab32 execution record — 17 September 2026

**Bounded Linux runtime: 27/27 assertions passed**, run `20260917T095248Z`.
The test used the exact subscriber.py, make-config.py, send-dynamic.py and topology
versions retained with their SHA256 hashes in that evidence directory.
Environment: WSL Ubuntu 26.04, Linux 6.18.33.2-microsoft-standard-WSL2,
iproute2 6.19.0, FreeRADIUS/radclient 3.2.8+dfsg-1ubuntu2. Already extracted tools
were copied privately; host package installation/services were not modified.
An iptables-restore alias and private dictionary/radclient wrapper adapt the
extracted binaries. Containerlab, Docker build and commercial NOS did not run.

Observed: unauthorised/wrong-password/unsupported-profile denial; authorisation
of two independent attachments; delegated-prefix metadata; separate 5/1 Mbit/s
HTB configuration objects; acknowledged Start/Interim/Stop; real CoA NAK for an
incorrect session, unsupported profile and stale timestamp; invalid authenticator
discard; CoA ACK with portal-only filtering; other subscriber unaffected;
restoration with unchanged session ID; forged-source denial and DROP counter2;
Disconnect ACK/old-session NAK; AAA outage denies new sessions while an existing
subscriber remains active; fresh authentication restores a new session ID;
explicit termination closes both attachments.

One established TCP echo connection passed before the change, timed out during
the garden restriction, and resumed after restoration. This proves the selected
flow could not bypass that policy. It does not show zero-loss profile changes or
a general continuity/timing guarantee. Rate configuration was inspected; no
Lab32 throughput benchmark was executed. Accounting has no byte counters or
billing-grade persistence/reconciliation. IPv6 forwarding is disabled and the
Delegated-IPv6-Prefix is metadata only.

Failed attempts retained: 094102 (missing extracted iptables-restore alias,
zero assertions); 094524 (missing explicitly configured reject module, one pass);
094610 (test expected the wrong tc JSON nesting, six passes); 094659 (test expected
a numeric error when radclient displayed its symbolic name, eight passes then
one failed assertion); 095114 (HTB root replace rejected live change, 13 passes
then one failure). The final helper removes/adds its owned root queue under a
temporarily closed attachment. Those prior runs are not relabelled successful.

Evidence includes exact runner/helpers, commands, RADIUS debug replies, account
journal/server detail and results.json. Generated secret files are not exported;
final debug logs redact their literal values. Dummy lab identities/passwords and
documentation addresses are intentionally visible. The fixture is not a complete
RADIUS conformance, protected-transport, replay, BNG scale, DHCP/PD or CGN test.
