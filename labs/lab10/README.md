# Lab 10 — Configuration state and recovery

This topology contains SR Linux 24.10.1 and FRR 10.2.1. The previous VyOS
container placeholder has been removed: a generic Linux container declaration
did not establish a supported VyOS appliance or the promised CLI behaviour.
Bring other platforms in through an appropriate appliance definition and
record the exact image, licence, interface mapping and configuration mode.

Validation status: topology and procedure reviewed statically; **not executed
on a Containerlab host during this edit**. Expected observations below are
acceptance criteria, not measured results. Before use, record the Containerlab
and Docker versions and the resolved image digests; tags alone are not immutable.

## Deploy and establish independent access

Run from this directory on a suitable isolated Linux lab host:

```bash
sudo containerlab deploy -t rosetta.clab.yml
sudo containerlab inspect -t rosetta.clab.yml
docker exec -it clab-lab10-srl sr_cli
```

Keep that container-console session open. Open a second terminal and a separate
SR Linux CLI session using the same command. This exercises independent CLI
sessions, not an independent physical management network. A host or Docker
failure affects both. If using SSH, obtain the assigned management address from
the inspect output and follow the image's credential policy.

Record the software version and the initial running interface description:

```text
show version
info from running /interface ethernet-1/1
```

The initial description should be `LAB10-BASELINE`. If deployment or a command
fails, stop the dependent test and record the error; do not count it as a pass.

## 10.1 — Compare application and persistence

On SR Linux, enter these commands as one configuration step:

```text
enter candidate
set / interface ethernet-1/1 description "LAB10-ACCEPTED"
diff
commit stay
```

From the other CLI session inspect the running interface. It should show the
new description. Back in the editing session, persist the running configuration:

```text
save startup
```

Check that the save succeeds. Persistence is a separate check from the running
value: inspect the saved configuration through the release's supported startup
configuration workflow, or restart only this disposable lab appliance while
retaining its generated configuration. Destroy-and-redeploy from the original
YAML is **not** a persistence test; that intentionally reinstates the baseline.

For comparison, enter FRR's CLI:

```bash
docker exec -it clab-lab10-frr vtysh
```

```text
configure terminal
interface eth1
 description LAB10-ACCEPTED
exit
end
show running-config
write memory
```

Record when each description became visible, what was persisted and where, and
the original value needed for undo. FRR's behaviour does not validate Cisco
syntax, hardware or reload recovery. Routing advertisements are outside this
lab; later routing labs add them with a defined peer and expected prefix set.

## 10.2 — Prove expiry and acceptance without breaking management

First return SR Linux to a known baseline and save it:

```text
enter candidate
set / interface ethernet-1/1 description "LAB10-BASELINE"
commit now
save startup
```

Then arm the trial. Start a stopwatch when the device reports successful commit:

```text
enter candidate
set / interface ethernet-1/1 description "LAB10-EXPIRY-TRIAL"
diff
commit confirmed timeout 60
```

Do not paste an acceptance command. From the independent session observe the
running description before expiry and again after the timer expires. The
expected values are `LAB10-EXPIRY-TRIAL`, then `LAB10-BASELINE`. Record the actual
times, device messages and values. Failure to observe either transition is a
failed or inconclusive test requiring investigation.

Repeat with description `LAB10-ACCEPT-TRIAL`. After observing it in the other
session, and **before** expiry, execute this in the trial session:

```text
commit confirmed accept
save startup
```

Check the acceptance and save results. Observe the running description after
the original deadline; it should remain `LAB10-ACCEPT-TRIAL`. Do not claim
startup persistence solely from that observation.

| Test | Required evidence | Actual result |
|---|---|---|
| Baseline | Image version and original description | Not run |
| Trial applied | Successful commit and new running value | Not run |
| Expiry | Timer elapsed and original value restored | Not run |
| Acceptance | Acceptance message and value after deadline | Not run |
| Persistence | Saved state or retained-config restart evidence | Not run |
| Cleanup | Baseline restored or topology destroyed | Not run |

An optional management-loss extension requires a release-specific, complete
ACL, a management source/interface inventory, and a previously proven console
recovery procedure. The old incomplete ACL and invented checkpoint command
have been removed. A description test proves the configuration timer only;
it does not prove traffic recovery, session survival or recovery from a crash.

## Cleanup

Restore the original description and save it, or destroy this named lab:

```bash
sudo containerlab destroy -t rosetta.clab.yml
```

Preserve your transcript and completed evidence table separately before cleanup.

## Primary references

- [SR Linux 24.10 CLI interface: commit options and acceptance](https://documentation.nokia.com/srlinux/24-10/books/system-mgmt/cli-interface.html)
- [SR Linux 24.10 configuration basics: startup persistence](https://documentation.nokia.com/srlinux/24-10/books/pdf/Configuration_Basics_Guide_24.10.pdf)
