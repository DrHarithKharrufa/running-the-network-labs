# A small automation kit with a narrow contract

These original teaching fixtures accompany AUT-01–12. `kit.py` never connects to
devices. Its contract is **one allowlisted description leaf** on one declared
lab interface. It is not a general configuration firewall or deployment system.

## Offline route

Use Python 3.11+ in a private virtual environment. Install the pinned
`requirements-controller.txt`, then run from this directory:

```text
python ci.py
python kit.py render --platform iosxe
python kit.py guard --platform iosxe
python kit.py event --platform iosxe
python netconf_edit.py --platform iosxe
```

Without `--observed`, guard/preflight/golden/event/diff/rollback commands run
labelled **synthetic offline acceptance fixtures** using their fixed fixture
clock. They do not certify current device state. `ci.py` runs every platform's
positive and refusal fixtures and checks XML wrappers, deletion inverses and
escaping. Its output explicitly says device_execution=false. The stored report
is an offline RUN only, never a device/vendor-panel RUN.

Templates use Jinja StrictUndefined. The narrow input schema refuses quotes,
backslashes, control characters, newline injection and unknown fields rather
than attempting to serialize arbitrary command strings. Render twice and compare
hashes. Review native context before using a fragment; templates contain no login,
commit, save or deployment command.

## Independent device observations

Copy `inventory.example.yml` into a protected local file, keep only **one**
platform/node and replace the documentation address and credential placeholders.
Record actual device/model/image, Python and collection/library versions.
Validate host keys and TLS hostnames/CA chains. Junos uses juniper.device.pyez;
SR Linux uses verified HTTPS JSON-RPC. Read the vendor baseline before enabling
a management service. `read-interface.yml` is a read-only example, run separately
from credential-free CI:

```text
ansible-playbook -i my-protected-inventory.yml read-interface.yml --limit r1_iosxe
```

Capture the **full owned configuration description and presence/absence**, plus
the interface's existence/status. A truncated operational description is not
complete state evidence. VyOS's show-configuration command can include other
configuration: scope/redact the retained transcript and never publish secrets.
Do not declare a missing getter healthy by substituting an empty dictionary.

For actual preflight/guard/compliance use a reviewed observation JSON with
synthetic=false, actual platform/device/interface, full original description,
presence flag, UTC timestamp, schema_version, independent management_ok and
service_ok, restoration_ready and the protected baseline SHA-256. Provide the
separately reviewed expected hash; copying the observed hash without review
does not establish freshness or authorization:

```text
python kit.py guard --platform iosxe --observed my-observed.json --expected-baseline REVIEWED_64_HEX_DIGEST
```

This uses the real UTC clock and refuses observations older than 300 seconds,
future timestamps, missing evidence and mismatched identity/hash. ALLOW means
the **scoped proposal** passed these rules; deployment_permission remains false.
`diff`/`rollback` produce an offline plan, not an executed recovery. For an
originally absent description, use `restoration-inverses.yml`; for an originally
present value, restore that exact value. Empty and absent are different states.
Junos's check/commit:false inverse is a preview; its live confirmed-commit phase
must be separately reviewed and verified. Preserve unrelated candidate changes.

## NETCONF transaction laboratory

`netconf_edit.py` supplies five native payload **adaptations** and filters:
IOS XE GigabitEthernet1/0/1 description; NX-OS existing nonforwarding po5 descr;
Junos ge-0/0/0 description; IOS XR active=act/GigabitEthernet0/0/0/0 description;
SR OS dedicated lab device system contact. Inspect namespaces, exact keys and
current server model revision. Well-formed XML is not server/YANG validation.
EOS has no qualified NETCONF variant in this edition.

The default command prints an offline preview and hash. Optional connected work
requires ncclient, a protected inventory, independently verified SSH host key,
actual model revision, recovery/service gates and credentials referenced by
environment-variable names. Never put the credentials into the shared inventory:

```json
{
  "platform": "iosxe",
  "host": "router-a.lab",
  "port": 830,
  "lab_owned": true,
  "known_host_key_verified": true,
  "expected_model_revision": "REPLACE_WITH_ACTUAL_SERVER_REVISION",
  "username_env": "WB_NETCONF_USER",
  "password_env": "WB_NETCONF_SECRET",
  "independent_service_check_ready": true,
  "restoration_tested": true
}
```

Capture the read-only owned baseline with `--capture-baseline --inventory FILE
--baseline FILE`. Review its original presence/value and hash. Then `--apply-lab`
requires those files and `--approved-sha256` matching the exact preview XML.
It refuses without candidate, validate and confirmed-commit capabilities. It
locks candidate and refuses prior candidate edits or a changed running baseline.
It does **not** fall back to writable running. The documented NX-OS example uses
running: an image lacking the stricter capabilities correctly remains NOT_RUN.

After edit/validate/confirmed commit, the script reads the label back and keeps
the **same NETCONF session alive**. Independently verify service, then acknowledge
the displayed hash-specific confirmation token within 60 seconds. No acknowledgement
means no confirmation; closing a nonpersistent confirmed-commit session can
revert immediately, before its 120-second timeout. Verify recovery independently.
An RPC error before commit discards only the candidate changes made after the
clean-candidate gate. No permanent-save operation is requested.

For restoration, `--restore` builds the original value or leaf-delete inverse.
Require a fresh reviewed baseline and inventory expected_current_label_sha256
matching the current owned state, preventing restoration over concurrent drift.
Review the inverse XML hash before the restore transaction. Preserve meaningful
leaf whitespace; normalization does not erase it.

## Event ledger and CI boundary

Real event planning additionally takes `--event FILE --ledger FILE` and actual
observed evidence. Events contain only event_id, device, interface, received_utc
and kind=interface-observation. They produce a read-only plan, never a shell
command. Duplicate IDs survive restart in the ledger, an exclusive file lock
serializes writers, a 30-second cooldown bounds repeated plans, and a full
1,000-ID ledger refuses new events. A stale lock requires inspection and manual
recovery; it is not automatically deleted. This is a bounded lab receiver design,
not a high-availability event platform. Authenticate the real event transport and
qualify its clock/skew and retention policy independently.

CI consists of local rendering and fixtures only; it has no device credentials,
live observations or deployment stage. Archive candidate/baseline/test hashes
and review them together. Library/version qualifications and commercial NOS
execution remain separate, explicitly unperformed acceptance steps.
