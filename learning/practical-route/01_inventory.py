"""Read a CSV table. No device connection is made."""
import csv
from pathlib import Path

path = Path(__file__).with_name('inventory.csv')
with path.open(newline='', encoding='utf-8') as source:
    devices = list(csv.DictReader(source))

for device in devices:
    name = device['asset_id']
    owner = device['owner']
    print(f'{name}: ask {owner}')
print(f'{len(devices)} devices inventoried')
