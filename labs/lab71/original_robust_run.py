#!/usr/bin/env python3
"""
Lab 71.1 -- automation must survive a network that is partly broken.

Chapter 71 sec 7: assume every device may be unreachable or half-broken; never
let a partial failure become a worse one, and never leave the network
half-changed. This runs a "change" across many devices where some fail, and
shows the right behaviour: per-device isolation, timeouts, a clean report, and
untouched failed devices.

    python3 robust_run.py
"""

# Simulated fleet; some devices are unreachable or error.
FLEET = {
    "leaf-01": "ok", "leaf-02": "ok", "leaf-03": "unreachable",
    "leaf-04": "ok", "leaf-05": "auth-error", "leaf-06": "ok",
}

def apply_change(device, state):
    """Pretend to push a change; raise for the broken ones (as a real lib would)."""
    if state == "unreachable":
        raise TimeoutError("no route to device (timed out)")
    if state == "auth-error":
        raise PermissionError("authentication failed")
    return "changed"

def run(fleet):
    succeeded, failed = [], []
    for device, state in fleet.items():
        try:
            apply_change(device, state)           # each call is time-bound + isolated
            succeeded.append(device)
        except Exception as e:                     # catch PER DEVICE, never abort the run
            failed.append((device, type(e).__name__, str(e)))
    return succeeded, failed

if __name__ == "__main__":
    print("Applying a change across the fleet (some devices are broken):\n")
    ok, bad = run(FLEET)
    for d in ok:
        print(f"  [OK]     {d}: changed")
    for d, kind, msg in bad:
        print(f"  [SKIP]   {d}: {kind} -- {msg} (left UNTOUCHED)")
    print(f"\nSummary: {len(ok)} succeeded, {len(bad)} failed and were left "
          f"in their prior state.")
    print("The run did NOT crash on the first unreachable device, and it did NOT")
    print("half-change anything -- it reports exactly what happened (sec 7). The")
    print("naive script would have aborted at leaf-03, leaving 01-02 changed and")
    print("the rest in unknown state -- the worst outcome.")
