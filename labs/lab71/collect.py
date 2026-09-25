"""Local parser demo, or one explicitly selected IOS CLI read via verified SSH."""
import argparse
from getpass import getpass
import ipaddress
import json
from pathlib import Path

REQUIRED = {"interface", "ip_address", "status", "proto"}

def validate_records(records, expected_interfaces):
    if not isinstance(records, list) or not records:
        raise ValueError("expected non-empty parsed rows; raw/empty output is not healthy state")
    if not expected_interfaces or len(set(expected_interfaces)) != len(expected_interfaces):
        raise ValueError("expected interfaces must be non-empty and unique")
    seen = set()
    for row in records:
        if not isinstance(row, dict) or not REQUIRED <= row.keys():
            raise ValueError("missing parser fields")
        if any(not isinstance(row[k], str) or not row[k].strip() for k in REQUIRED):
            raise ValueError("wrong field type or empty field")
        if row["interface"] in seen:
            raise ValueError("duplicate interface")
        seen.add(row["interface"])
        if row["ip_address"] != "unassigned":
            ipaddress.IPv4Address(row["ip_address"])
        if row["status"] not in {"up", "down", "administratively down"} or row["proto"] not in {"up", "down"}:
            raise ValueError("unsupported status value; inspect raw evidence and parser contract")
    if not set(expected_interfaces) <= seen:
        raise ValueError("expected interface absent")
    return records  # A valid 'down' row remains down; schema acceptance is not health.

def parse_fixture():
    from netmiko.utilities import get_structured_data_textfsm
    text = Path(__file__).with_name("ios-show-ip-interface-brief.txt").read_text("utf-8")
    rows = get_structured_data_textfsm(text, platform="cisco_ios", command="show ip interface brief", raise_parsing_error=True)
    return validate_records(rows, ["GigabitEthernet0/0", "GigabitEthernet0/1"])

def collect_one(host, user, password, known_hosts, expected_interfaces):
    from netmiko import ConnectHandler
    with ConnectHandler(device_type="cisco_ios", host=host, username=user,
                        password=password, ssh_strict=True, alt_host_keys=True,
                        alt_key_file=str(known_hosts), conn_timeout=10,
                        auth_timeout=10, banner_timeout=10) as conn:
        rows = conn.send_command("show ip interface brief", read_timeout=20,
                                 use_textfsm=True, raise_parsing_error=True)
    return validate_records(rows, expected_interfaces)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="omit for the offline synthetic fixture")
    parser.add_argument("--user")
    parser.add_argument("--known-hosts", type=Path)
    parser.add_argument("--expect", action="append", help="expected interface; repeat for more")
    args = parser.parse_args()
    if not args.host:
        if args.user or args.known_hosts or args.expect:
            parser.error("connection options require --host")
        rows = parse_fixture()
        scope = "Synthetic local fixture; no connection or device verification"
    else:
        if not args.user or not args.expect or not args.known_hosts or not args.known_hosts.is_file():
            parser.error("explicit user, existing verified known-hosts file and expected interfaces required")
        # Errors are surfaced without including raw exception/session contents or secrets.
        try:
            rows = collect_one(args.host, args.user, getpass("SSH password: "), args.known_hosts, args.expect)
        except Exception as exc:
            print(json.dumps({"error_type": type(exc).__name__, "status": "COLLECTION_FAILED"}))
            return 1
        scope = "CLI read and parser contract only; inspect status fields for health"
    print(json.dumps({"scope": scope, "records": rows}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
