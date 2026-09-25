#!/usr/bin/env python3
"""Lab 79: isolated Linux namespace implementation of the worked design.

Requires root, iproute2, iputils ping and Linux network namespaces. Creates only
four uniquely named namespaces and internal veth pairs; never attaches a host or
physical interface. JSON is written to stdout after owned namespaces are removed.
"""
import argparse
import json
import os
import platform
import subprocess
import time
import uuid


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="create isolated namespaces and run acceptance tests")
    args = ap.parse_args()
    if not args.run:
        print(json.dumps({"status": "NOT_RUN", "scope": __doc__})); return 0
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        raise SystemExit("Run on Linux as root; see README. No namespace was created.")
    prefix = "rtn79-" + uuid.uuid4().hex[:8]
    ns = {key: prefix + "-" + key for key in ("hl", "rl", "rm", "hm")}
    owned = []
    log = []
    assertions = []
    timings = []
    report = {"status": "FAILED", "scope": "Linux namespace forwarding only; no NOS/hardware/carrier/availability evidence",
              "kernel": platform.release(), "python": platform.python_version(), "namespaces": ns,
              "commands": log, "assertions": assertions, "reachability_checks_seconds": timings}

    def command(argv, *, check=True, timeout=10):
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        log.append({"argv": argv, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
        if check and p.returncode:
            raise RuntimeError(f"command failed: {argv}: {p.stderr}")
        return p

    def ip(key, *args):
        return command(["ip", "-n", ns[key], *args])

    def execute(key, *args, **kwargs):
        return command(["ip", "netns", "exec", ns[key], *args], **kwargs)

    def expect(name, condition):
        assertions.append({"name": name, "passed": bool(condition)})
        if not condition: raise AssertionError(name)

    def ping(key, destination, *, success=True):
        p = execute(key, "ping", "-n", "-c", "3", "-i", "0.1", "-W", "1", destination, check=False)
        expect(f"{key} to {destination}: {'reachable' if success else 'unreachable'}",
               p.returncode == 0 if success else p.returncode == 1)
        if success:
            expect("all three probes received", " 0% packet loss" in p.stdout)

    def path(expected):
        for key, destination in (("rl", "10.79.20.10"), ("rm", "10.79.10.10")):
            lookup = json.loads(ip(key, "-j", "route", "get", destination).stdout)
            expect(key + " selected " + expected, lookup[0]["dev"] == expected)

    def pair(a, ia, aa, b, ib, ab):
        # Both ends are created directly inside the owned namespaces.
        ip(a, "link", "add", ia, "type", "veth", "peer", "name", ib, "netns", ns[b])
        for key, interface, address in ((a, ia, aa), (b, ib, ab)):
            ip(key, "address", "add", address, "dev", interface)
            ip(key, "link", "set", interface, "up")

    def restore_routes():
        # Linux removes static routes bound to an administratively down device.
        # Bringing its interface up is not a configuration reconciler.
        for key, target, next_a, next_b in (("rl", "10.79.20.0/24", "10.79.0.2", "10.79.0.6"),
                                           ("rm", "10.79.10.0/24", "10.79.0.1", "10.79.0.5")):
            for device, hop, metric in (("wan-a", next_a, "100"), ("wan-b", next_b, "200")):
                ip(key, "route", "replace", target, "via", hop, "dev", device, "metric", metric)

    def recovered_after_down(interface, expected):
        start = time.monotonic()
        ip("rl", "link", "set", interface, "down")
        # This measures admin-down command start through successful lookup/probes,
        # not the packet-loss interval or a distribution of convergence times.
        path(expected)
        ping("hl", "10.79.20.10"); ping("hm", "10.79.10.10")
        elapsed = time.monotonic() - start
        timings.append({"fault": "rl admin-down " + interface, "elapsed": elapsed})
        expect("acceptance commands finish within 5-second lab allowance", elapsed < 5)
        ip("rl", "link", "set", interface, "up")
        restore_routes()
        path("wan-a")

    try:
        report["iproute2"] = command(["ip", "-Version"]).stdout.strip()
        report["ping"] = command(["ping", "-V"]).stdout.strip()
        for key in ns:
            command(["ip", "netns", "add", ns[key]])
            owned.append(ns[key]); ip(key, "link", "set", "lo", "up")
        pair("hl", "eth0", "10.79.10.10/24", "rl", "lan", "10.79.10.1/24")
        pair("rl", "wan-a", "10.79.0.1/30", "rm", "wan-a", "10.79.0.2/30")
        pair("rl", "wan-b", "10.79.0.5/30", "rm", "wan-b", "10.79.0.6/30")
        pair("rm", "lan", "10.79.20.1/24", "hm", "eth0", "10.79.20.10/24")
        for key in ("rl", "rm"):
            execute(key, "sysctl", "-qw", "net.ipv4.ip_forward=1")
            for interface in ("all", "default", "lan", "wan-a", "wan-b"):
                execute(key, "sysctl", "-qw", "net.ipv4.conf." + interface + ".rp_filter=0")
                execute(key, "sysctl", "-qw", "net.ipv4.conf." + interface + ".ignore_routes_with_linkdown=1")
        ip("hl", "route", "add", "default", "via", "10.79.10.1")
        ip("hm", "route", "add", "default", "via", "10.79.20.1")
        restore_routes()
        report["lld_state"] = {key: {"addresses": json.loads(ip(key, "-j", "address").stdout),
                                    "routes": json.loads(ip(key, "-j", "route").stdout)} for key in ns}
        for key in ("rl", "rm"):
            expect(key + " has no default route", all(r["dst"] != "default" for r in report["lld_state"][key]["routes"]))
        path("wan-a"); ping("hl", "10.79.20.10"); ping("hm", "10.79.10.10")
        recovered_after_down("wan-a", "wan-b")
        recovered_after_down("wan-b", "wan-a")
        # Explicit boundary: both transits down is not covered by R2.
        for interface in ("wan-a", "wan-b"): ip("rl", "link", "set", interface, "down")
        ping("hl", "10.79.20.10", success=False)
        for interface in ("wan-a", "wan-b"): ip("rl", "link", "set", interface, "up")
        restore_routes()
        path("wan-a"); ping("hl", "10.79.20.10")
        report["status"] = "PASSED"
    except Exception as exc:
        report["error"] = repr(exc)
    finally:
        report["cleanup"] = []
        for name in reversed(owned):
            p = command(["ip", "netns", "del", name], check=False)
            report["cleanup"].append({"namespace": name, "returncode": p.returncode})
        remaining = command(["ip", "netns", "list"]).stdout
        report["owned_namespaces_removed"] = all(name not in {line.split()[0] for line in remaining.splitlines() if line} for name in owned)
        if not report["owned_namespaces_removed"] or any(x["returncode"] for x in report["cleanup"]):
            report["status"] = "FAILED"
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__": raise SystemExit(main())
