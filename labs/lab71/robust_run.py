#!/usr/bin/env python3
"""Offline failure simulation. No sockets, SSH, NOS or service verification."""
import argparse
import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import runpy

BASELINE = {"description": "before", "mtu": 1500}
DESIRED = {"description": "after", "mtu": 1600}
FAULTS = {"ok", "reject", "before-timeout", "after-timeout", "partial-timeout", "unobservable"}

@dataclass
class Device:
    name: str
    fault: str = "ok"
    state: dict = field(default_factory=lambda: dict(BASELINE))
    writes: int = 0

    async def apply(self):
        self.writes += 1
        if self.fault == "reject":
            raise PermissionError("simulated rejection before mutation")
        if self.fault == "before-timeout":
            await asyncio.sleep(3600)
        if self.fault == "partial-timeout":
            self.state["description"] = DESIRED["description"]
            await asyncio.sleep(3600)
        self.state.update(DESIRED)
        if self.fault in {"after-timeout", "unobservable"}:
            await asyncio.sleep(3600)

    async def read(self):
        if self.fault == "unobservable":
            await asyncio.sleep(3600)
        return dict(self.state)

async def run_fleet(fleet, *, policy="dependent", max_incidents=1,
                    timeout=0.05, restore_partial=False):
    """Actual local coroutine deadlines; remote cancellation is NOT modelled."""
    if policy not in {"dependent", "independent"}:
        raise ValueError("unknown policy")
    if type(max_incidents) is not int or max_incidents < 1:
        raise ValueError("max_incidents must be a positive integer")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    if len({d.name for d in fleet}) != len(fleet) or any(d.fault not in FAULTS for d in fleet):
        raise ValueError("duplicate identity or unknown fault")
    results = []
    incidents = 0
    for device in fleet:
        result = {"device": device.name, "history": ["NOT_STARTED"],
                  "observed": None, "incident": False}
        if incidents >= max_incidents or (policy == "dependent" and incidents):
            result["status"] = "NOT_STARTED"
            results.append(result)
            continue
        baseline = deepcopy(device.state)  # simulator's pre-change observation
        result["history"].append("STARTED")
        try:
            await asyncio.wait_for(device.apply(), timeout)
            result["history"].append("APPLIED_ACKNOWLEDGED")
        except PermissionError:
            result["history"].append("REJECTED")
            result["incident"] = True
        except TimeoutError:
            result["history"].append("UNKNOWN")
            result["incident"] = True
        # A fresh observation, not the exception type, determines visible state.
        try:
            observed = await asyncio.wait_for(device.read(), timeout)
            result["observed"] = observed
            if observed == DESIRED:
                status = "VERIFIED_SCOPE"
            elif observed == baseline:
                status = "BASELINE_OBSERVED"
                result["incident"] = True
            else:
                status = "PARTIAL_OBSERVED"
                result["incident"] = True
                if restore_partial:
                    # Explicit teaching recovery policy, not a device rollback RPC.
                    device.state = dict(baseline)
                    observed = await asyncio.wait_for(device.read(), timeout)
                    result["observed"] = observed
                    status = "ROLLED_BACK_SCOPE" if observed == baseline else "UNKNOWN"
        except TimeoutError:
            status = "UNKNOWN"
            result["incident"] = True
        result["history"].append(status)
        result["status"] = status
        results.append(result)
        incidents += result["incident"]
    # Ground truth is exposed for learners only, never used to claim an unread result.
    return {"scope": "Offline two-field configuration simulation; no service/NOS evidence",
            "policy": policy, "incidents": incidents, "results": results,
            "simulator_truth": {d.name: dict(d.state) for d in fleet},
            "write_attempts": {d.name: d.writes for d in fleet}}

def demonstration_fleet():
    return [Device("leaf-01"), Device("leaf-02", "after-timeout"),
            Device("leaf-03", "partial-timeout"), Device("leaf-04", "unobservable"),
            Device("leaf-05", "reject"), Device("leaf-06", "before-timeout"),
            Device("leaf-07")]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=["dependent", "independent"], default="dependent")
    parser.add_argument("--max-incidents", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=0.05, help="local coroutine deadline, seconds")
    parser.add_argument("--restore-partial", action="store_true", help="enable simulated baseline restoration")
    parser.add_argument("--demo-original", action="store_true", help="run the retained flawed historical demonstration")
    args = parser.parse_args(argv)
    if args.demo_original:
        print("HISTORICAL FLAWED DEMO: its untouched-device and timeout claims are invalid.")
        runpy.run_path(str(Path(__file__).with_name("original_robust_run.py")), run_name="__main__")
        return 0
    try:
        report = asyncio.run(run_fleet(demonstration_fleet(), policy=args.policy,
                                     max_incidents=args.max_incidents, timeout=args.timeout,
                                     restore_partial=args.restore_partial))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 0 if not report["incidents"] and all(r["status"] == "VERIFIED_SCOPE" for r in report["results"]) else 1

if __name__ == "__main__":
    raise SystemExit(main())
