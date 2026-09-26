"""Validate addresses before selecting a target. Values are documentation IPs."""
import csv
import ipaddress
from pathlib import Path


def validate_inventory(rows):
    seen_ids, seen_addresses = set(), set()
    for row in rows:
        address = ipaddress.ip_address(row['management_ip'])
        network = ipaddress.ip_network(row['prefix'], strict=True)
        if address not in network:
            raise ValueError(f'{address} is outside {network}')
        if row['asset_id'] in seen_ids or address in seen_addresses:
            raise ValueError('duplicate asset or management address')
        if not row['owner'].strip(): raise ValueError('missing owner')
        seen_ids.add(row['asset_id'])
        seen_addresses.add(address)
    if not rows: raise ValueError('empty inventory')
    return rows


if __name__ == '__main__':
    with Path(__file__).with_name('inventory.csv').open(newline='') as source:
        devices = validate_inventory(list(csv.DictReader(source)))
    print(f'Validated {len(devices)} unique targets; no connections made')
