# Lab 58.1–58.2 — records parsed, and signatures made and broken

```bash
python3 dmarc_check.py              # what the published records say
python3 dkim_alignment.py           # DKIM signed, verified and broken; DMARC alignment
python3 dkim_alignment.py --crosscheck
python3 test_dmarc_check.py         # 120 checks
python3 test_dkim_alignment.py      # 62 checks
```

Both run offline in a container. **No message was sent anywhere, no DNS was
queried, and no mail provider was contacted.** Where a receiver's behaviour
matters — whether it honours `p=reject`, what it does with a forwarded message —
that is policy, not arithmetic, and these labs say so rather than guessing.

## 58.1 — the check that accepted the word "present"

The version that shipped tested `bool(spf)` and `bool(dkim)`. Any non-empty
string counted as a record, and its own worked example passed the literal string
`"present"` as the DKIM record. It then printed, for records it had never
parsed:

> `-> Enforcing: spoofing of this domain is actively rejected. Good.`

Three falsehoods in one line. The records were never validated. **Quarantine is
not rejection** — and the same branch printed this for `p=quarantine`. And no
published record rejects anything: rejection is a receiver's decision.

The rebuilt version parses. It requires `v=DMARC1` first (a DMARC record whose
version tag is not first is not a DMARC record, and receivers ignore it
silently), rejects duplicate tags, validates every value against the
specification, and diagnoses a misspelled `policy=` rather than quietly
treating the record as policy-free. For SPF it counts the **DNS-lookup terms
against the limit of ten** — the single most common way a working record
silently becomes a permerror as includes accumulate — catches `+all`, flags
`ptr`, and recognises two published SPF records as the permerror they are. For
DKIM it recognises an **empty `p=`** as a revoked key rather than as a present
one.

It reports three states, not a boolean: `ABSENT`, `INVALID`, `VALID`. And it
never says a message would be accepted or rejected.

## 58.2 — what a DKIM signature actually proves

This one executes. Real 2048-bit RSA keys, RFC 6376 relaxed canonicalisation,
real signatures:

| case | result |
|---|---|
| the message as signed | verifies |
| one digit of the bank account changed | fails |
| the Subject changed | fails |
| signed by a different key | fails |
| **`l=` set, and text appended** | **verifies** |
| **a `Reply-To` added that was never in `h=`** | **verifies** |

The last two are the point. `l=` tells the verifier to hash only the first *n*
octets, so anything appended after them is unsigned and passes anyway. And `h=`
lists what is covered — a header that is not in it can be added or altered by
anyone on the path. "DKIM passed" is not the same as "the message you are
reading was signed".

Then alignment, which is the question DMARC actually asks:

```
  scenario                                                 DMARC
  sent directly from an authorised server                  PASS
  forwarded by the recipient to another address            PASS   (SPF failed; aligned DKIM carried it)
  through a mailing list that rewrites the Subject         FAIL   (DKIM broke; SPF aligned to the list)
  a bulk provider signing with its own domain              FAIL   (both pass, neither aligns)
  the same, signing as mail.acme.example                   PASS
  subdomain signing under a strict policy (adkim=s)        FAIL
```

And the message that passes everything while being exactly what the reader was
worried about:

```
  From: Acme Finance <billing@acme-invoices.example>
  DKIM verifies: True    DMARC: PASS
```

Every check passes, because every check evaluates the domain **the attacker
registered**. `acme.example` may publish `p=reject`; it is never consulted,
because nothing in the message claims to be `acme.example`. The reader sees
"Acme Finance".

### Why you should believe any of this

An implementation that only agrees with itself has proved something about
itself. `--crosscheck` verifies our signature with **dkimpy**, an independent
implementation, and confirms that it rejects the tampered copy. When dkimpy is
not installed the check reports that it **skipped** — a skipped check is not a
passed one.

## What to take away

- A published record is a statement about DNS. Whether a message passes is a
  question about a message.
- SPF authenticates the envelope sender's IP. DKIM authenticates what `h=` and
  `l=` cover, under one `d=`. Neither mentions the From: header the reader sees.
- DMARC is the alignment check. A pass for an unaligned domain is not a pass.
- `p=reject` closes one door: direct spoofing of your exact domain. Lookalike
  domains, display names and compromised authorised senders all walk past it.
