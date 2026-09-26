"""A decoded object is not yet a valid observation."""
import json
from pathlib import Path
from common import validate_snapshot


def report(snapshot):
    validate_snapshot(snapshot)
    rows=[]
    for interface in snapshot['interfaces']:
        packets=interface['packets']
        ratio=None if packets==0 else interface['errors']/packets
        rows.append({'interface':interface['name'], 'state':interface['oper_state'],
                     'error_ratio':ratio})
    return {'asset_id':snapshot['asset_id'], 'interfaces':rows}


if __name__=='__main__':
    data=json.loads(Path(__file__).with_name('snapshot.json').read_text())
    print(json.dumps(report(data),indent=2))
