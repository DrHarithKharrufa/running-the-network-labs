# Labs 69.1 and 69.2 - deterministic rendering and bounded application tests

The original entry point is repaired in place. The original programme is preserved
as `original_one_template_four_vendors.py`; `--demo-original` reproduces its flawed
SR Linux syntax and false "idempotent render" claim for comparison.

## Lab 69.1: one intent with four explicit mappings

Use Python 3.12+ in a local virtual environment and the pinned `requirements.txt`.
Jinja2 is 3.1.6, MarkupSafe 3.0.3. Ansible is needed only for Lab 69.2.

```
python one_template_four_vendors.py
python -m unittest -v test_rendering.py
```

`INTENT` describes an untagged access attachment to the teaching service VLAN30.
It does not invent a universal port-numbering scheme. `TARGETS` supplies explicit
interface names and documentation profiles:

| Profile | Example interface | Representation |
|---|---|---|
| Catalyst 9300, IOS XE 17.15 | GigabitEthernet1/0/8 | VLAN object and switchport access mode |
| Arista EOS 4.36.2F Ethernet ports | Ethernet8 | VLAN object and switchport access mode |
| Nokia SR Linux 24.10, 7220 IXR | ethernet-1/8.0 | Untagged bridged subinterface attached to a mac-vrf |
| Junos ELS on an EX switch | ge-0/0/8.0 | VLAN object and ethernet-switching access membership |

These are documentation-scoped candidate fragments. Confirm the exact hardware,
release, port, features and existing state before any isolated-device test. The
Junos profile covers the cited ELS command family; no specific Junos runtime release
has been verified. A new vendor can require changing the intent/capability model,
not just adding a template.

The SR Linux example enables VLAN classification on the physical interface and
uses `vlan encap untagged` on a bridged subinterface. Its network-instance name
`VLAN30` is the local service label; **it does not make ingress frames carry tag 30**.
No IRB, EVPN, VXLAN or remote bridging is configured. The common demonstration is
untagged service attachment, not equivalence for every tagged/priority-tagged frame
or vendor default. IOS XE/EOS explicitly enter switched access mode. Junos uses
ELS `interface-mode access`, not the older `port-mode` syntax.

Every candidate is a fragment. Administrative state, port security, spanning tree,
management, complete routing and full Anvil fabric configuration are not supplied
by this small example. Reusing a port previously configured for another mode can
require removal of old state. The renderer does not calculate those transitions.

Unknown modes, missing/extra fields, unsupported targets, invalid VLANs and unsafe
description delimiters are rejected. Jinja uses `StrictUndefined`. Render twice:
equal bytes demonstrate **determinism**. They do not demonstrate device parser
acceptance, idempotent application, convergence or forwarding.

## Lab 69.2: execute Ansible on localhost

Controller: Linux or WSL; pinned `ansible-core==2.21.4`. No vendor collection is
required for this local-file exercise. From the lab directory, choose a private
scratch output path that does not already hold another document:

```
ansible-playbook -i localhost, render.yml --syntax-check
ansible-playbook -i localhost, render.yml --check --diff
ansible-playbook -i localhost, render.yml
ansible-playbook -i localhost, render.yml
```

The default destination is `rendered-iosxe.cfg` next to the playbook. On WSL use a
Linux-filesystem destination for mode tests, for example with
`-e '{"output_file":"/tmp/rtn-lab69-candidate.cfg"}'`. The template task writes only
this local file, with mode 0600. It never connects to a device. Check mode on a fresh
destination predicts a change without creating the file; the first actual run
creates it; the second should report zero changes with identical contents. This
demonstrates application idempotency **for this local file resource**.

Append a harmless synthetic comment to the file. Check mode should report the diff
without repairing it; an actual run restores the intended content. Change VLAN to
40 with `-e '{"vlan":40}'`: the complete local file is replaced and the old access
VLAN line disappears. This replacement behaviour belongs to the `template` module;
it is not evidence that `ios_config src` replaces a whole device configuration.
Invalid mode/VLAN/description input must fail before changing the file.

## Optional device application experiment - separate evidence

`device-experiment.yml` is a guarded IOS XE description-only example, not executed
by the offline/local-file lab. Its documentation targets are `cisco.ios==11.5.1`
and `ansible.netcommon==8.6.2` in `collections.yml`. Pin the controller, transport
library, collection, device model and exact NOS release in any actual run record.
Install the transport requirements of the selected plugin. The example does not
render or deploy a complete leaf configuration.

Build a one-host inventory group `iosxe_lab` from an approved snapshot; inspect it
with `ansible-inventory --list` and verify the target address and interface. Give it
only authorised lab credentials through an SSH agent or secret mechanism. Independently
verify the SSH host-key fingerprint and populate known_hosts. Keep host-key checking
enabled and set `ANSIBLE_HOST_KEY_AUTO_ADD=false`; do not auto-trust an unknown key.
The guards additionally require `lab_authorised=true`, `approved_target`,
`intent_revision` and an equal `approved_revision`. These inputs are a workflow
guard, not an authentication or authorisation service.

On an isolated supported IOS XE switch with the selected interface, retain:

1. The pre-change configuration/operational evidence and restoration plan. The
   play owns only the selected interface description. Protect full backups because
   they may contain credentials; the example does not print or make such a backup.
2. A check/diff run and the reviewed proposed command. Confirm the task/collection
   contracts; check mode is not a general guarantee that every playbook task is read-only.
3. First actual application and independent read-back of the description.
4. Second application: expected `changed=false`, no relevant state change and no
   unexpected side effects. A reported flag alone is insufficient.
5. A deliberate description drift, its detection and correction; then restore the
   original description or remove it explicitly if originally absent. Test this
   removal separately, because omission from an additive snippet is not deletion.
6. Service checks and the agreed persistence policy. `save_when: never` leaves
   startup configuration untouched in this example; it is not a rollback mechanism.

Do not claim device idempotency from two dry runs: neither dry run establishes a
converged device state. Broader access/routed transitions and complete replacement
need their own isolated platform tests. No commercial NOS or forwarding execution
is included in the current local evidence.

## Primary references

- [IOS XE 17.15 Catalyst 9300 VLAN guide](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-15/configuration_guide/vlan/b_1715_vlan_9300_cg.pdf)
- [Arista EOS Data Transfer, 4.36.2F at access](https://www.arista.com/en/um-eos/eos-data-transfer)
- [SR Linux 24.10 subinterface VLAN configuration](https://documentation.nokia.com/srlinux/24-10/books/interfaces/subinterface-vlan-configuration.html)
- [SR Linux 24.10 network instances](https://documentation.nokia.com/srlinux/24-10/books/config-basics/network-instances.html)
- [Junos interface-mode, ELS](https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/interface-mode-edit-interfaces.html)
- [Junos bridging and VLANs](https://www.juniper.net/documentation/us/en/software/junos/multicast-l2/topics/topic-map/bridging-and-vlans.html)
- [cisco.ios.ios_config](https://docs.ansible.com/projects/ansible/latest/collections/cisco/ios/ios_config_module.html)
- [Check and diff modes](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html)
- [network_cli requirements and host-key controls](https://docs.ansible.com/projects/ansible/latest/collections/ansible/netcommon/network_cli_connection.html)
- [Jinja API: StrictUndefined](https://jinja.palletsprojects.com/en/stable/api/)

Accessed 24 September 2026. Live documentation may change; the named versions and
recorded local environment delimit the evidence.
