#!/usr/bin/env python3
"""Lab 77: bounded assurance over synthetic, supplied evidence; no network I/O."""
from copy import deepcopy
from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
import runpy


@dataclass(frozen=True)
class Intent:
    endpoints: tuple = ("LON-probe", "MAN-probe")
    traffic_class: str = "interactive"
    rtt_limit_ms: float = 50.0  # strict <; normal operation only
    restoration_limit_ms: float = 50.0  # strict <; per supplied trial
    demand_gbps: float = 60.0
    utilisation_limit: float = 0.70  # inclusive <=
    window_seconds: int = 300
    sample_count: int = 300
    snapshot_max_age: int = 60
    trial_max_age: int = 86400
    minimum_paths: int = 2

    def __post_init__(self):
        if (not isinstance(self.endpoints, tuple) or len(self.endpoints) != 2
                or not all(isinstance(s, str) and s for s in self.endpoints)
                or len(set(self.endpoints)) != 2
                or not isinstance(self.traffic_class, str) or not self.traffic_class):
            raise ValueError("two distinct named endpoints and a traffic class required")
        for name in ("rtt_limit_ms", "restoration_limit_ms", "demand_gbps"):
            if not number(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(name)
        if not number(self.utilisation_limit) or not 0 < self.utilisation_limit <= 1:
            raise ValueError("utilisation_limit")
        for name in ("window_seconds", "sample_count", "snapshot_max_age", "trial_max_age", "minimum_paths"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(name)


def number(v):
    return type(v) in (int, float) and math.isfinite(v) and v >= 0


def assure(intent, observed, *, now):
    """A known breach wins over unknowns; MET requires all supplied checks complete.

    Snapshot evidence is assessed together: malformed/stale/wrong-target snapshots
    cannot supply a trustworthy breach either. Fault trials are checked separately.
    Capacity is an ideal pool model; no routing, queues, packet loss or packet I/O.
    """
    if not isinstance(intent, Intent) or not number(now):
        raise ValueError("valid Intent and finite nonnegative clock required")
    result = {"status": "UNKNOWN", "scope": "synthetic evidence and ideal pool model only",
              "violations": [], "unknowns": [], "checks": {}}
    unknown = result["unknowns"]
    breaches = result["violations"]
    checks = result["checks"]
    try:
        if not isinstance(observed, dict):
            raise ValueError("observation must be an object")
        for name in ("source", "topology_revision"):
            if not isinstance(observed[name], str) or not observed[name]:
                raise ValueError(f"missing {name}")
        if (observed["endpoints"] != list(intent.endpoints)
                or observed["traffic_class"] != intent.traffic_class):
            raise ValueError("wrong endpoints or traffic class")
        end = observed["window_end"]
        start = observed["window_start"]
        if (not number(end) or not number(start) or end - start != intent.window_seconds
                or not 0 <= now - end <= intent.snapshot_max_age):
            raise ValueError("stale/future/malformed observation window")
        samples = observed["rtt_samples_ms"]
        if (not isinstance(samples, list) or len(samples) != intent.sample_count
                or not all(number(x) for x in samples)):
            raise ValueError("missing or invalid RTT samples")
        paths = observed["paths"]
        if not isinstance(paths, list) or not paths:
            raise ValueError("missing path inventory")
        ids = set()
        for p in paths:
            if (not isinstance(p, dict) or not isinstance(p["id"], str) or not p["id"]
                    or p["id"] in ids or type(p["up"]) is not bool
                    or not number(p["capacity_gbps"]) or p["capacity_gbps"] <= 0
                    or not isinstance(p["srlgs"], list) or not p["srlgs"]
                    or not all(isinstance(s, str) and s for s in p["srlgs"])
                    or len(p["srlgs"]) != len(set(p["srlgs"]))):
                raise ValueError("invalid path inventory")
            ids.add(p["id"])
        if observed["srlg_inventory_complete"] is not True:
            raise ValueError("SRLG mapping completeness not asserted")
    except (KeyError, TypeError, ValueError) as e:
        unknown.append(f"snapshot: {e}")
        return result

    rtt = sorted(samples)[math.ceil(0.95 * len(samples)) - 1]
    checks["normal_rtt_p95_ms"] = rtt
    if rtt >= intent.rtt_limit_ms:
        breaches.append("normal RTT p95 is not strictly below its limit")
    active = [p for p in paths if p["up"]]
    checks["active_paths"] = len(active)
    if len(active) < intent.minimum_paths:
        breaches.append("fewer active paths than the normal-operation requirement")
    # Scope: each single named path, and each single declared shared risk.
    faults = {"path:" + p["id"]: {p["id"]} for p in paths}
    for risk in sorted({r for p in paths for r in p["srlgs"]}):
        faults["srlg:" + risk] = {p["id"] for p in paths if risk in p["srlgs"]}
    capacity = {}
    for fault, removed in {"normal": set(), **faults}.items():
        usable = sum(p["capacity_gbps"] for p in active if p["id"] not in removed) * intent.utilisation_limit
        capacity[fault] = usable
        if intent.demand_gbps > usable:
            breaches.append(f"{fault}: usable pool {usable:g} Gbit/s below demand")
    checks["usable_capacity_gbps"] = capacity

    trials = observed.get("fault_trials")
    if not isinstance(trials, dict):
        unknown.append("fault-trial evidence missing")
        trials = {}
    for fault in faults:
        try:
            trial = trials[fault]
            at = trial["at"]
            values = trial["restoration_ms"]
            if (trial["topology_revision"] != observed["topology_revision"]
                    or not number(at) or not 0 <= now - at <= intent.trial_max_age
                    or not isinstance(values, list) or not values
                    or not all(number(v) for v in values)):
                raise ValueError("stale, mismatched or invalid trial")
            checks.setdefault("maximum_supplied_restoration_ms", {})[fault] = max(values)
            if max(values) >= intent.restoration_limit_ms:
                breaches.append(f"{fault}: supplied restoration trial meets/exceeds strict limit")
        except (KeyError, TypeError, ValueError) as e:
            unknown.append(f"{fault}: {e}")
    result["status"] = "VIOLATED" if breaches else ("UNKNOWN" if unknown else "MET")
    return result


def fixture():
    """Constructed values, not readings or executed fault trials."""
    obs = {"source": "synthetic-fixture-v1", "topology_revision": "r1",
           "endpoints": ["LON-probe", "MAN-probe"], "traffic_class": "interactive",
           "window_start": 670, "window_end": 970, "rtt_samples_ms": [22.0] * 300,
           "srlg_inventory_complete": True,
           "paths": [{"id": "A", "up": True, "capacity_gbps": 100, "srlgs": ["duct-a"]},
                     {"id": "B", "up": True, "capacity_gbps": 100, "srlgs": ["duct-b"]}]}
    obs["fault_trials"] = {key: {"at": 900, "topology_revision": "r1", "restoration_ms": [24, 26, 29]}
                           for key in ("path:A", "path:B", "srlg:duct-a", "srlg:duct-b")}
    return obs


def scenarios():
    normal = fixture()
    down = deepcopy(normal); down["paths"][1]["up"] = False
    shared = deepcopy(normal)
    for p in shared["paths"]: p["srlgs"] = ["shared-duct"]
    shared["fault_trials"]["srlg:shared-duct"] = {"at": 900, "topology_revision": "r1", "restoration_ms": [120]}
    small = deepcopy(normal); small["paths"][1]["capacity_gbps"] = 50
    latency = deepcopy(normal); latency["rtt_samples_ms"] = [50.0] * 300
    slow = deepcopy(normal); slow["fault_trials"]["path:A"]["restoration_ms"] = [50.0]
    stale = deepcopy(normal); stale["window_start"] = 500; stale["window_end"] = 800
    return {"normal": normal, "one link down": down, "shared duct": shared,
            "survivor too small": small, "RTT equals limit": latency,
            "restoration equals limit": slow, "stale": stale}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo-original", action="store_true")
    args = ap.parse_args()
    if args.demo_original:
        print("HISTORICAL FLAWED DEMO: booleans and printed actions do not establish assurance.")
        runpy.run_path(str(Path(__file__).with_name("assurance_original.py.txt")), run_name="__main__")
    else:
        print(json.dumps({name: assure(Intent(), obs, now=1000) for name, obs in scenarios().items()}, indent=2))
