# Lab 52 — the management plane, with two of three labs executed

| | What it does | Evidence category |
|---|---|---|
| 52.1 `access_audit.py` | Audits a *description* and certifies nothing | Static review of a dictionary |
| 52.2 `tacacs_obfuscation.py` | Runs the TACACS+ construction and breaks it | **Linux execution** |
| 52.3 `ssh_revocation.py` | Real CA, real certificates, real KRL | **Linux execution** |

```bash
python3 access_audit.py         # and --json
python3 tacacs_obfuscation.py   # and --json
python3 ssh_revocation.py       # and --json  (needs openssh-client)

python3 test_access_audit.py         # 86 checks
python3 test_tacacs_obfuscation.py   # 77 checks
python3 test_ssh_revocation.py       # 64 checks
```

227 checks in total. **52.3 requires `ssh-keygen`** and refuses to simulate
without it — a lab that fakes an execution it could not perform is worse than
one that stops.

## 52.1 — why this one was rebuilt

The shipped audit failed **open** in three ways.

**Presence was read as adequacy.** `if m["break_glass_tested_days_ago"] is None`
raised a finding on an empty field — right direction — but *any number silenced
it*. A break-glass path last tested nine hundred days ago audited as
satisfactory. The script asked whether a field was **populated**, not whether its
value was **acceptable**.

**Truthiness was read as a control.** `if m["session_recording"]:` printed an OK
for any truthy value, so `"planned"` would have been recorded as a control in
place.

**And the whole thing was a blocklist.** `if m["secrets_location"] ==
"git-repo"` fires on one known-bad value. Write anything else — `"vault"`, `"a
share everyone can read"`, `"not sure"` — and **no finding fires at all**, which
reads as approval.

Underneath all three sits the finding the rebuild is named for: **a script cannot
certify a control from a label.** It is reading a description somebody typed. So
the rebuilt version sorts that description into three piles and never prints OK:

```
  4 finding(s), 4 unanswered, 0 claimed, 0 CERTIFIED
```

`CERTIFIED` is zero and always will be. `UNSTATED` means the model did not
answer, or gave an answer the check does not recognise — **not a pass**. And
`CLAIMED` rows carry the evidence that would settle them: not "session recording:
OK" but "the model says so; retrieve a recording for a named session, and show
the policy that stops an administrator deleting their own."

Two rows that used to be silent now fire. `break_glass_tested_days_ago: 900` is a
finding. `ssh_model: certificates` is **UNSTATED**, because certificates alone do
not answer the question — see 52.3.

## 52.2 — TACACS+ does not encrypt

The chapter said TACACS+ "encrypts the whole payload" where RADIUS encrypts only
the password. The comparison is right and the word is wrong. TACACS+ applies an
**obfuscation**: a keystream chained from MD5 over the session id, the shared
key, the version and the sequence number, XORed over the body.

**The keystream depends on nothing secret per message.** Two bodies under the
same session and sequence share a pad exactly:

```
  attacker knew       status=FAIL   msg=command not permitted for role
  attacker recovered  status=PASS   msg=command permitted by policy
  recovery exact: True,  key used: False
```

**The body is malleable.** A denial becomes a permission:

```
  the server said       status=FAIL   msg=command not permitted for role
  the device now reads  status=PASS   msg=command not permitted for role
  bytes changed 3, length unchanged True, key used False
  integrity field present    False
```

Three bytes, not four — FAIL and PASS share a letter, and the edit is bounded by
the difference between the words rather than their length.

**And there is no integrity field**: the header carries a length, not a MAC.

What this does **not** say: it is not an attack on any deployment (every byte is
synthetic), and it is **not** a claim that RADIUS is better — RADIUS obfuscates
only the password attribute and gives no per-command authorisation, so the
chapter's preference for TACACS+ in device administration stands. What changes is
the word, and therefore what you must add. TACACS+ over TLS does not have these
properties, which is the point: **the transport supplies them, not the protocol**.

None of the three failures depends on MD5 being weak. They are properties of a
keystream XOR with no per-message secret and no integrity field, and a stronger
hash changes none of them.

## 52.3 — revoking one person, not the whole team

The chapter recommended certificates over authorised-keys files, correctly, and
invited a wrong conclusion: *revoke the CA relationship and the leaver is out.*

Removing the CA from `TrustedUserCAKeys` revokes **every certificate that CA ever
issued**:

```
  leaver           alice
  loses access     alice, bob, carol  (3 people)
  also locked out  bob, carol
```

On the night somebody leaves, that is the whole team locked out by the control
meant to remove one person.

**A KRL is the mechanism that revokes one holder** — executed with real OpenSSH:

```
  alice    REVOKED   alice-cert.pub (alice): REVOKED
  bob      ok        bob-cert.pub (bob): ok
  carol    ok        carol-cert.pub (carol): ok
```

Its cost: the KRL is a **file**. It works on devices holding the current copy, so
revocation becomes a distribution problem with the same reach as the CA estate,
and a device that missed the update still accepts the leaver.

**Short lifetimes revoke by expiry** — nothing has to reach the devices, but the
leaver keeps access until the certificate runs out, and the issuing service is now
on the critical path for every login, every few hours, for ever.

Three mechanisms, **two of which revoke a person**. Choosing between them is a
choice about which operational burden you would rather carry. "Use certificates"
names neither.

## What none of this establishes

- **52.1 audits a description, not an estate.** No device, bastion, directory,
  vault or log is touched. Everything it calls CLAIMED is a sentence somebody
  typed, and the script cannot tell a true claim from a hopeful one.
- **52.2 involved no TACACS+ server, client, device or capture.** Every byte is
  synthetic and no real shared secret exists in the file. An on-path position is
  assumed throughout, and obtaining one is a separate problem — which is exactly
  what the out-of-band network exists to make harder.
- **52.3 opens no socket and runs no sshd.** It shows what the certificate
  *tooling* reports about a credential; whether a given server enforces that is
  its configuration — `TrustedUserCAKeys`, `RevokedKeys`, clock accuracy,
  principals — and none of that is tested. The KRL's distribution is not modelled.
- **No maturity score, percentage or grade** appears anywhere. A count of
  findings against a count of questions is not a percentage of security.
