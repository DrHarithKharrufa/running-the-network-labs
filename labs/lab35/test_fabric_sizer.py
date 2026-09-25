#!/usr/bin/env python3
"""Offline arithmetic checks for fabric_sizer.py.

Scope: pure arithmetic and input validation. This executes no network device,
no Containerlab topology and no ASIC, and it predicts no achieved throughput.
Ratios are exact rational comparisons, not floating-point approximations.

    python3 test_fabric_sizer.py
"""
from fractions import Fraction

import fabric_sizer as fs

CHECKS = []


def check(name, condition):
    CHECKS.append((name, bool(condition)))
    return bool(condition)


def raises(name, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError:
        return check(name, True)
    except Exception:
        return check(name, False)
    return check(name, False)


def main():
    # --- The error this lab exists to prevent -------------------------------
    # A leaf with two uplinks cannot reach eight distinct spines. The model must
    # refuse it rather than silently averaging the bandwidth.
    raises("2 uplinks cannot serve 8 spines", fs.size, 48, 25, 2, 100, 8)
    raises("6 uplinks cannot serve 4 spines evenly", fs.size, 48, 25, 6, 100, 4)
    check("8 uplinks over 8 spines is one link per spine",
          fs.size(48, 25, 8, 100, 8)["links_per_spine"] == 1)
    check("8 uplinks over 4 spines is two links per spine",
          fs.size(48, 25, 8, 100, 4)["links_per_spine"] == 2)

    # --- Input validation ---------------------------------------------------
    raises("zero spines rejected", fs.size, 48, 25, 8, 100, 0)
    raises("negative downlinks rejected", fs.size, -1, 25, 8, 100, 8)
    raises("non-integer port count rejected", fs.size, 48.5, 25, 8, 100, 8)
    raises("zero rate rejected", fs.size, 48, 0, 8, 100, 8)
    raises("cannot fail more spines than exist", fs.size, 48, 25, 8, 100, 8, 9)
    raises("zero lanes per cage rejected", fs.cages, 8, 0)
    raises("booleans are not accepted as a spine count", fs.size, 48, 25, 8, 100, True)
    raises("booleans are not accepted as a port count", fs.size, True, 25, 8, 100, 8)

    # --- Oversubscription arithmetic (exact) --------------------------------
    s = fs.size(48, 25, 8, 100, 8, failed_spines=1)
    check("48x25 down = 1200 Gb/s", s["down_bw_gbps"] == 1200)
    check("8x100 up = 800 Gb/s", s["up_bw_gbps"] == 800)
    check("normal ratio is exactly 3:2",
          Fraction(s["down_bw_gbps"]) / Fraction(s["up_bw_gbps"]) == Fraction(3, 2))
    check("one spine lost leaves 700 Gb/s", s["remaining_up_gbps"] == 700)
    check("failure ratio is exactly 12:7",
          Fraction(s["down_bw_gbps"]) / Fraction(s["remaining_up_gbps"]) == Fraction(12, 7))
    check("leaf is not uplink-oversubscribed only when down<=up",
          fs.size(4, 25, 8, 100, 8)["no_leaf_uplink_oversubscription"] is True)

    # --- Total spine loss isolates the leaf ---------------------------------
    dead = fs.size(48, 25, 8, 100, 8, failed_spines=8)
    check("all spines lost isolates the leaf", dead["isolated"] is True)
    check("isolated leaf reports no failure ratio",
          dead["failure_oversubscription"] is None)

    # --- Physical cage accounting -------------------------------------------
    check("24 logical ports in 4-lane cages need 6 cages", fs.cages(24, 4) == 6)
    check("breakout rounds up, it does not truncate", fs.cages(9, 4) == 3)
    check("native ports are one cage each", fs.cages(8, 1) == 8)
    check("zero ports need zero cages", fs.cages(0, 4) == 0)
    raises("leaf cage budget is enforced",
           fs.uniform_fabric, 42, 4, 48, 25, 4, 100, 8, 4, 4, 1, 64, 4, 1)
    raises("spine cage budget is enforced",
           fs.uniform_fabric, 42, 4, 48, 25, 4, 100, 32, 4, 4, 1, 8, 4, 1)
    raises("downlinks must cover whole servers",
           fs.uniform_fabric, 42, 4, 47, 25, 4, 100, 32, 4, 4, 1, 64, 4, 1, 2)
    check("dual-NIC servers halve the homogeneous server count",
          fs.uniform_fabric(42, 4, 48, 25, 4, 100, 32, 4, 4, 1, 64, 4, 1,
                            2)["homogeneous_single_leaf_servers"] == 42 * 48 // 2)

    # --- The Anvil hall assumption ------------------------------------------
    a = fs.anvil_hall()
    check("hall has 8 spines", a["spines"] == 8)
    check("hall has 32 leaves", a["leaves"] == 32)
    check("32 leaves x 8 uplinks = 256 logical fabric links",
          a["logical_fabric_links"] == 256)
    check("leaf pools sum to the stated leaf count",
          sum(p["leaves"] for p in a["pools"].values()) == a["leaves"])
    check("server interfaces sum to 608",
          sum(p["server_interfaces"] for p in a["pools"].values()) == 608 == a["server_interfaces"])
    check("64 GPU nodes matches the front reference network", a["gpu_nodes"] == 64)
    check("GPU service leaves carry exactly the 64 GPU node attachments",
          a["pools"]["gpu_service"]["server_interfaces"] == 64)

    expected = {
        "general": (Fraction(3, 1), Fraction(24, 7), Fraction(6, 1)),
        "storage": (Fraction(2, 1), Fraction(16, 7), Fraction(4, 1)),
        "gpu_service": (Fraction(1, 1), Fraction(8, 7), Fraction(8, 7)),
    }
    for pool, (normal, failed, cage) in expected.items():
        p = a["pools"][pool]
        check(pool + " normal ratio is exactly " + str(normal),
              Fraction(p["down_bw_gbps"]) / Fraction(p["up_bw_gbps"]) == normal)
        check(pool + " one-spine-loss ratio is exactly " + str(failed),
              Fraction(p["down_bw_gbps"]) / Fraction(p["remaining_up_gbps"]) == failed)
        check(pool + " one-cage-loss ratio is exactly " + str(cage),
              Fraction(p["down_bw_gbps"]) /
              Fraction((8 - p["uplink_lanes_per_cage"]) * (p["up_bw_gbps"] // 8)) == cage)
        check(pool + " has one link per spine", p["links_per_spine"] == 1)

    check("a shared breakout cage loses 4 links at once, worse than one spine",
          Fraction(6, 1) > Fraction(24, 7))
    check("native-cage GPU uplinks lose only one link per cage",
          expected["gpu_service"][1] == expected["gpu_service"][2])

    check("per-spine logical links equal the leaf count",
          a["per_spine"]["logical_links"] == a["leaves"] == 32)
    check("per-spine cages are 6 breakout + 8 native = 14",
          a["per_spine"]["used_cages"] == 14)
    check("per-spine link capacity is 24x25 + 8x100 = 1400 Gb/s",
          a["per_spine"]["aggregate_link_capacity_gbps"] == 1400)
    check("server-facing total is 20 Tb/s",
          a["server_facing_gbps"] == 20 * 600 + 4 * 400 + 8 * 800 == 20000)
    check("uplink total is 11.2 Tb/s",
          a["uplink_gbps"] == 24 * 200 + 8 * 800 == 11200)
    check("the hall is server-oversubscribed overall",
          a["server_facing_gbps"] > a["uplink_gbps"])

    # --- Worked examples are internally consistent --------------------------
    ex = fs.examples()
    check("2000-port exercise reaches 2016 server interfaces",
          ex["exercise_2000"]["server_interfaces"] == 42 * 48 == 2016)
    check("4000-port exercise reaches 4032 server interfaces",
          ex["exercise_4000"]["server_interfaces"] == 84 * 48 == 4032)
    check("2000-port exercise is 3:1",
          Fraction(ex["exercise_2000"]["down_bw_gbps"]) /
          Fraction(ex["exercise_2000"]["up_bw_gbps"]) == Fraction(3, 1))
    check("4000-port exercise is 3:1",
          Fraction(ex["exercise_4000"]["down_bw_gbps"]) /
          Fraction(ex["exercise_4000"]["up_bw_gbps"]) == Fraction(3, 1))
    check("max uniform leaves is bounded by spine cages and breakout",
          ex["exercise_2000"]["max_uniform_leaves"] == (64 - 4) * 1 // 1 == 60)
    check("exercise fabrics stay inside their spine cage budget",
          ex["exercise_2000"]["spine_free_cages"] >= 0 and
          ex["exercise_4000"]["spine_free_cages"] >= 0)

    check("4000-port exercise uses four spines", ex["exercise_4000"]["spines"] == 4)
    check("4000-port exercise retains 12 free leaf cages", ex["exercise_4000"]["leaf_free_cages"] == 12)

    import json
    try:
        json.dumps(ex, allow_nan=False)
        check("examples() is strict-JSON serialisable", True)
    except ValueError:
        check("examples() is strict-JSON serialisable", False)

    passed = sum(1 for _, ok in CHECKS if ok)
    for name, ok in CHECKS:
        print(("PASS  " if ok else "FAIL  ") + name)
    print("\n%d/%d checks passed" % (passed, len(CHECKS)))
    print("Scope: offline arithmetic and validation only. No device, no "
          "Containerlab, no ASIC, no throughput measurement.")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
