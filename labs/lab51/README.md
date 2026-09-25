# Lab 51 — cryptography, mostly executed rather than modelled

Four programs. Unlike most labs in this book, **most of this one runs for real**:
real keys, real ciphertexts, real digests, a real forgery, real TLS 1.3
handshakes on loopback. Where something is described rather than executed, it
says so in the output.

| | What it does | Evidence category |
|---|---|---|
| 51.1 `primitives.py` | Malleability, AEAD nonce reuse, a keyed-hash forgery | **Linux execution** (A–C), offline calculation (D) |
| 51.2 `forward_secrecy.py` | The compromise model, ephemeral vs static vs PSK | **Linux execution** (A–B), static review (C–D) |
| 51.3 `pqc_inventory.py` | Migration exposure by cryptographic role | Offline calculation over stated scenarios |
| 51.4 `tls_validation.py` | Ten certificate and chain cases on loopback | **Linux execution** |

```bash
pip install -r requirements.txt

python3 primitives.py         # and --json
python3 forward_secrecy.py    # and --json
python3 pqc_inventory.py      # and --json
python3 tls_validation.py     # emits JSON; exit code is the verdict

python3 test_primitives.py        # 195 checks
python3 test_forward_secrecy.py   # 200 checks
python3 test_pqc_inventory.py     # 119 checks
python3 test_tls_validation.py    #  71 checks
```

585 checks in total.

## 51.1 — three things done, not described

**Encryption alone does not protect what the message says.** A stream cipher
turns a known plaintext position into an editable one:

```
  before  AUTH role=operator prefix-limit=00100 peer=198.51.100.7
  after   AUTH role=rootadmn prefix-limit=99999 peer=198.51.100.7
```

No key. Twelve bytes of ciphertext changed, length identical, and the recipient
decrypted it **without any error at all**. The same edit against AES-GCM is
rejected.

**AEAD has a condition the chapter never stated.** Repeat a nonce under one key
and the XOR of two ciphertexts is the XOR of two plaintexts:

```
    attacker already knew  'GET /status HTTP/1.1\r\nHost: router-01.example\r'
    attacker recovered     'PASS admin:Tr0ub4dor&3 enable:H0rseBattery!!\r\n'
    recovery exact: True, key used: False
```

And confidentiality is the first thing to go, not the only thing — a repeated
nonce leaks information about the GCM authentication subkey, so enough repeats
buy forgery as well as reading.

**"MD5 authentication" is several constructions, and one of them forges.** This
is the section worth running yourself:

```
  construction under attack   H(key || message)
  attacker saw the key        False
  original message            prefix=10.0.0.0/8 nexthop=192.0.2.1 metric=10
  attacker appended            prefix=0.0.0.0/0 nexthop=198.51.100.66 metric=1
  forged authenticator        dd773971eaa384dc9c282a9fef667e08
  key holder would compute    dd773971eaa384dc9c282a9fef667e08
  FORGERY SUCCEEDS            True
  same attack against HMAC    False
```

A Merkle–Damgård digest **is** the hash's internal state after the last block,
so publishing the digest publishes the state. The attacker resumes from it,
appends a default route pointing at themselves, and produces an authenticator
that verifies — having never held the key.

And the upgrade everyone reaches for first, **executed rather than assumed**:

```
    hand-written SHA-256 matches hashlib on 9/9 vectors: True
    SHA-256 in H(key || message), forgery succeeds: True
    HMAC-SHA-256, forgery succeeds:                 False
```

Swapping MD5 for SHA-256 inside the same construction fixes **nothing**. The
property belongs to Merkle–Damgård, and SHA-256 is Merkle–Damgård too. What
fixes it is changing the *construction*.

**Quantum computers do not halve hash security, once.** The halving rule
describes preimage search and nothing else:

```
output      preimage  w/Grover   collision     w/BHT
256-bit         256       128        128       85
```

Collision resistance was already n/2 classically, from the birthday bound. And
Grover does not parallelise the way money does — classical search divides by the
number of machines, Grover by the *square root*:

```
      machines    classical       Grover  advantage
           2^0       256.0        128.0      128.0
          2^40       216.0        108.0      108.0
```

The last two columns are identical in every row, and that is an identity: the
advantage is `(n − log₂P) − (n/2 − ½log₂P)`, which simplifies to the Grover
exponent itself.

## 51.2 — forward secrecy answers exactly one question

Same attacker, handed the same material — both long-term private keys and the
full recorded handshake — against two designs:

```
  ephemeral agreement  8 agreements tried, recovered: False
  static agreement     8 agreements tried, recovered: True
      the static one fell to: server_long_term_private x client_long_public
```

**Nothing is asserted to be unrecoverable.** The attacker enumerates every key
agreement they can form from what they hold and derives a candidate from each;
eight attempts in both cases. The ephemeral session survives all eight because
the halves that contributed were discarded.

The same for resumption, which is where TLS 1.3 gets interesting:

```
  psk_ke      (PSK alone)         1 derivations tried, recovered: True
  psk_dhe_ke  (PSK + fresh share)  5 derivations tried, recovered: False
```

**TLS 1.3 has three key-exchange modes and one has no forward secrecy.**
`psk_ke` derives everything from the pre-shared secret, so whoever obtains that
secret later opens every session that used it. "TLS 1.3 gives you forward
secrecy" is true of two modes and false of the third — and **this script did not
measure which mode any deployment negotiates**, because Python's `ssl` does not
expose that choice. Section C is read from the specification and labelled as
such.

What the property does **not** cover, each with its reason: an endpoint
compromised at the time, a predictable RNG, session keys deliberately exported
to a monitoring appliance, long-lived resumption material, and traffic analysis.

## 51.3 — three quantities, kept apart

The worksheet this replaces applied `lifetime + migration >= horizon` to every
row, with one `lifetime` field, and got three things wrong.

**It applied a confidentiality inequality to signatures.** Mosca's inequality
works because ciphertext can be stored now and opened later. **A signature has
no such exposure** — you cannot retroactively forge one you recorded. The model
now refuses a signature row that supplies `data_confidentiality_years`, and
refuses a confidentiality row that supplies none.

**It discarded urgency on the two rows that needed it most.** `aes256` and
`unknown` returned their statuses *before* any lifetime test ran, so a
hundred-year confidentiality requirement against a one-year horizon came back
looking like somebody else's problem.

**And it had no way to express a dependency.** AES-256 at rest is exactly as
post-quantum as whatever wraps its key:

```
  Backup payload encryption              wrapping          22.0
      -> exposed_through_dependency
  Backup key wrapping                    unresolved        22.0
      -> identify_now_exposure_exceeds_horizon
```

Two rows describing one system. The old worksheet returned "separate symmetric
review" and "inventory required" — neither saying the system was exposed.

Using the session duration instead of the confidentiality lifetime:

```
  system                              session data life  correct if session
  VPN carrying patient records         0.0010      15.0  AT RISK       ok
  Management API long-lived secrets    0.0200      10.0  AT RISK       ok
```

**Two of four confidentiality rows flip from AT RISK to ok.**

And what cannot wait for a vendor roadmap:

```
  Firmware verification root in silicon
    rsa_signature, verifier in service 12 years, horizon 10
    status: decide_before_shipping_cannot_be_updated
    decision deadline: 0 years from now
```

"Wait for the vendors" is sound for things that can be changed later. A
verification root fixed in silicon at manufacture has no update path, so the
choice is made when the part is specified.

## 51.4 — a valid signature chain is not a valid certificate chain

Ten cases, executed against a real TLS 1.3 handshake on loopback. Each
rejection is pinned to its OpenSSL verification code, because a case rejected
for the *wrong* reason still shows `accepted=False` and demonstrates nothing —
one case in the first draft did exactly that and was rebuilt.

```
  untrusted_issuer                 code=20  unable to get local issuer certificate
  wrong_dns_name                   code=62  Hostname mismatch
  expired                          code=10  certificate has expired
  not_yet_valid                    code=9   certificate is not yet valid
  wrong_extended_key_usage         code=26  unsuitable certificate purpose
  leaf_used_as_issuer              code=79  invalid CA certificate
  path_length_exceeded             code=25  path length constraint exceeded
  intermediate_without_cert_sign   code=79  invalid CA certificate
```

**Seven of the eight rejections involve a chain in which every signature is
cryptographically valid** — and the test file verifies that independently, by
checking each certificate's signature against its issuer's public key rather
than taking the lab's word for it.

Validating a certificate is not checking a chain of signatures. It is checking a
chain of signatures **and** the constraints each certificate carries about what
it may be used for, by whom, for which name, and for how long.

## What none of this establishes

- **No network device, routing daemon or vendor implementation was involved.**
  51.1 demonstrates properties of *constructions*; which construction any given
  product uses is a question for that product's documentation, and several
  different ones travel under the name "MD5 authentication".
- **A forged authenticator is a necessary step, not a completed attack.**
  Whether the extended message is accepted depends on the protocol parser, the
  length fields and any replay protection, none of which is modelled.
- **A failure to recover is a failure by *this* attacker with *this* material.**
  It is evidence about a construction, not a proof that no attack exists.
- **51.2's Section C is not executed.** Which TLS 1.3 mode a deployment
  negotiates is answered by its configuration or a captured handshake.
- **51.3 predicts nothing about quantum hardware.** Every horizon is a stated
  scenario, every lifetime and dependency is a stated input about a fictional
  estate, and no output is a compliance decision.
- **51.4 checks no revocation**, measures no performance, and tests nothing
  about forward secrecy.
- The lab was exercised on `cryptography` 46.0.7 and OpenSSL 3.0.13; each run
  records the versions it actually used, which may differ from the pin in
  `requirements.txt`.
