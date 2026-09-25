# Lab 68.1 - intended data, observations and reviewed reconciliation

This repairs the shipped entry point. It remains a **local teaching model**.
No NetBox server, device, NOS parser, forwarding plane or configuration write is
executed by the default commands. Python 3.10+ and its standard library suffice.

```
python render_from_sot.py
python netbox_readonly.py
python -m unittest -v test_sot.py
python render_from_sot.py --demo-original
```

`original_render_from_sot.py` is the preserved flawed programme. Its statement that
the model must win is historical evidence, not operational advice.

## Model contract

The intended record has an owner, integer version, approval time, platform and
interfaces. Observations have a collection time, provenance and completeness flag.
The deterministic clock in the exercise is 24 September 2026 at 10:00 UTC; it does
not purport to be a live device observation. With default inputs the description
diff produces `REVIEW_REQUIRED`. Nothing is pushed or written back.

Unknown platforms/modes, inconsistent mode fields, invalid VLANs, unsupported
interface names and invalid IPv4 host prefixes fail validation. The renderer
accepts a deliberately narrow Ethernet-interface subset for `arista_eos`; it is
not a universal interface parser. It emits both `switchport` and
`switchport mode access` before selecting the access VLAN. Create/verify the VLAN,
port capabilities, existing configuration, service impact and rollback separately.
The fragment does not configure routing, remove obsolete addresses, transition
every possible prior port mode or replace a complete device configuration. Only
fresh reviewed changes may enter a separately authorised deployment workflow.

Arista command reference consulted: [EOS 4.36.2F Data Transfer](https://www.arista.com/en/um-eos/eos-data-transfer)
(accessed 24 September 2026). This is documentation review, not EOS execution.

The drift comparison includes added/removed interfaces and fields. An observed-only
field is a question about management scope, not an instruction to delete it. Stale,
future, incomplete or conflicting observations, version mismatch and an emergency
exception block reconciliation. A matching comparison means only no drift in the
supplied scope. Input dictionaries remain unchanged.

`duplicate_hosts` illustrates **ordinary unicast host allocation policy**, not the
NetBox validator. The tests select uniqueness for global and named namespaces;
permit the same address across different VRFs; and distinguish duplicate hosts
from different hosts inside nested prefixes. Shared-address roles are outside this
function. In NetBox 4.3.7, the VRF `enforce_unique` field and global
`ENFORCE_GLOBAL_UNIQUE` setting affect uniqueness. IP roles can permit intentional
duplicates. Prefix nesting is not generally forbidden by uniqueness enforcement.
See the pinned [VRF documentation](https://github.com/netbox-community/netbox/blob/v4.3.7/docs/models/ipam/vrf.md),
[global setting](https://github.com/netbox-community/netbox/blob/v4.3.7/docs/configuration/miscellaneous.md)
and [IP model validation](https://github.com/netbox-community/netbox/blob/v4.3.7/netbox/ipam/models/ip.py).

## Reproducible API illustration

Documentation target: **NetBox 4.3.7**, pinned for reproducibility, not a deployment
version recommendation. `api-fixtures.json` has two synthetic, projected JSON pages
for `GET /api/dcim/interfaces/?device_id=1&limit=1&ordering=id`. It is not a server
capture or a complete serializer dump. The client follows `next` and returns IDs
11 and 18; tests reject repeated IDs, changing counts, missing pages, cycles and
cross-origin links. Count/ID checks cannot establish an atomic database snapshot.
Use a controlled export/version or repeat a consistent read before deployment.

The built-in fields illustrated are `id`, `device`, `name`, `type`, `enabled`,
`description`, `mode`, `untagged_vlan` and `last_updated`. **`interface_role` is a
custom choice field**, created for `dcim.interface` with choices `uplink` and
`server`; it is not a built-in wired-interface role. In this fixture, `mode: null`
is not proof of routing state; the intended design and a separate IP-address
assignment record are needed. IP assignments are retrieved separately through
`/api/ipam/ip-addresses/` and related using object type and ID. The fixture client
does not join those objects or convert API responses into deployable configuration.

`last_updated` records database-object changes, not a telemetry collection time.
`exported_at` and `intent_version` are lab envelope metadata, not built-in interface
fields. The model's `collected_at` remains a separate observation timestamp.

Optional live read (not executed for this review): use an authorised lab server
running the named version and inspect its `/api/schema/swagger-ui/`. Grant the
account only view access to required interfaces and related data. Create an expiring
token with **write enabled deselected**, with allowed client addresses where useful.
Set `NETBOX_TOKEN` in the local environment without committing or printing it, then:

```
python netbox_readonly.py --live "https://YOUR-LAB-HOST/api/dcim/interfaces/?device_id=1&limit=1&ordering=id"
```

Replace the host and device ID. HTTPS certificate and hostname verification stay
enabled; install the lab CA in the appropriate trust store. There is no insecure
TLS option. Only GET is used, with time and response-size bounds; redirects and
cross-origin/other-endpoint pagination are rejected before credentials are sent.
Token permissions and server behaviour require independent verification. An API
read may update server access logs/token last-use metadata.

[Pinned NetBox REST API documentation](https://github.com/netbox-community/netbox/blob/v4.3.7/docs/integrations/rest-api.md).
No token, live server result or production inventory is included.

## Exercises

1. Add an observed-only interface and an obsolete field; explain who decides whether
   either belongs in the managed scope.
2. Make an observation older than the intent approval, then mark an emergency
   exception. Explain why automatic re-push would be unsafe in each case.
3. Repeat an address within and across VRFs. Document which uniqueness settings and
   shared-address roles a real NetBox deployment uses before relying on validation.
4. Change the second API page's count, ID or origin. Explain why a client must fail
   instead of silently accepting a partial or mixed inventory.
