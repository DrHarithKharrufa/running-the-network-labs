#!/usr/bin/env python3
"""
Lab 73.1 -- a validation pipeline, cheap checks first.

Chapter 73 sec 8: order the pipeline cheap-fast to expensive-slow, so a bad
change is rejected as early and cheaply as possible and only survivors reach the
costly stages. This runs a proposed change through lint -> policy-as-code ->
reachability ("Batfish"-style) -> canary, stopping at the first failure.

    python3 pipeline.py
"""

# A proposed change: a set of config lines for a device.
GOOD_CHANGE = [
    "interface Ethernet8",
    " description server-07",
    " switchport access vlan 30",
]
BAD_POLICY_CHANGE = [
    "line vty 0 4",
    " transport input telnet",          # violates 'no telnet' policy (cheap to catch)
    "interface Ethernet8",
    " description server-07",
]
BAD_REACH_CHANGE = [
    "interface Ethernet1",
    " ip address 10.200.1.1/31",
    "ip access-list EDGE",
    " deny ip any any",                  # well-formed but breaks reachability (dear to catch)
]

def lint(change):
    for ln in change:
        if ln and not ln[0].isalnum() and not ln.startswith(" "):
            return False, f"malformed line: {ln!r}"
    return True, "ok"

def policy(change):
    text = "\n".join(change)
    if "transport input telnet" in text:
        return False, "policy violation: telnet is forbidden (sec 3)"
    return True, "ok"

def reachability(change):
    # stand-in for Batfish (sec 4): a deny-any on the edge blackholes traffic
    if any("deny ip any any" in ln for ln in change):
        return False, "reachability regression: edge ACL denies all (Batfish would flag)"
    return True, "ok"

def canary(change):
    return True, "deployed to 1 canary device, telemetry nominal (sec 7)"

STAGES = [("lint (ms)", lint), ("policy-as-code (ms)", policy),
          ("reachability/Batfish (s)", reachability), ("canary (min)", canary)]

def run(name, change):
    print(f"[{name}]")
    for stage_name, fn in STAGES:
        ok, msg = fn(change)
        mark = "PASS" if ok else "FAIL"
        print(f"  {stage_name:26} {mark}  {msg}")
        if not ok:
            print(f"  -> rejected at '{stage_name}' -- cheap stages caught it first (sec 8)\n")
            return
    print("  -> all stages passed; change promoted to the fleet\n")

if __name__ == "__main__":
    print("Validation pipeline: fail fast and cheap (sec 8)\n")
    run("good change", GOOD_CHANGE)
    run("telnet change (caught cheaply by policy)", BAD_POLICY_CHANGE)
    run("edge deny-all (well-formed, caught by reachability)", BAD_REACH_CHANGE)
    print("The telnet change dies in milliseconds at policy; the deny-all is")
    print("well-formed (passes lint and policy) and is caught only by the dearer")
    print("reachability analysis -- which is why cheap checks run first.")
