#!/usr/bin/env python3
"""
Lab 68.1 -- intended state renders config; observed state reveals drift.

Chapter 68: the source of truth holds INTENDED state and the network reports
OBSERVED state; reconciliation compares them and, per data type, decides who
wins. This models a tiny source of truth, renders intended config, compares it
to observed state, and applies the reconciliation policy.

    python3 render_from_sot.py
"""

# --- the source of truth: INTENDED state (sec 2) ---
SOT = {
    "ald-leaf-01": {
        "role": "leaf", "site": "lon",
        "interfaces": {
            "Ethernet1": {"desc": "to-spine-1", "mode": "routed", "ip": "10.200.1.1/31"},
            "Ethernet8": {"desc": "server-07",  "mode": "access", "vlan": 30},
        },
    },
}

# --- what the device actually reports: OBSERVED state (sec 2) ---
OBSERVED = {
    "ald-leaf-01": {
        "interfaces": {
            "Ethernet1": {"desc": "to-spine-1", "mode": "routed", "ip": "10.200.1.1/31"},
            "Ethernet8": {"desc": "TEMP hand-edit", "mode": "access", "vlan": 30},  # drift!
        },
    },
}

# reconciliation policy: for automated data types, the MODEL wins (sec 7)
MODEL_WINS = {"desc", "mode", "vlan", "ip"}

def render(device):
    lines = []
    for name, i in SOT[device]["interfaces"].items():
        lines.append(f"interface {name}")
        lines.append(f" description {i['desc']}")
        if i["mode"] == "access":
            lines.append(f" switchport access vlan {i['vlan']}")
        else:
            lines.append(f" no switchport\n ip address {i['ip']}")
    return "\n".join(lines)

def reconcile(device):
    drift = []
    for name, want in SOT[device]["interfaces"].items():
        have = OBSERVED[device]["interfaces"].get(name, {})
        for key, wval in want.items():
            hval = have.get(key)
            if hval != wval:
                winner = "model -> re-push" if key in MODEL_WINS else "network -> update SoT"
                drift.append((name, key, wval, hval, winner))
    return drift

if __name__ == "__main__":
    dev = "ald-leaf-01"
    print(f"Rendered config for {dev} from the source of truth (intended state):\n")
    print(render(dev))
    print("\nReconciliation against observed state (sec 7):\n")
    d = reconcile(dev)
    if not d:
        print("  no drift.")
    for name, key, want, have, winner in d:
        print(f"  DRIFT {name}.{key}: intended={want!r} observed={have!r}")
        print(f"        policy: {winner}")
    print("\nThe hand-edited description is drift; because 'desc' is a model-wins")
    print("data type, reconciliation re-pushes intended state (sec 7). If the SoT")
    print("had merely discovered the network, it would now believe the hand-edit.")
