"""Calculate a change without applying it."""
import json
from common import request, validate_snapshot


def plan(snapshot, description):
    validate_snapshot(snapshot)
    if not isinstance(description,str) or not 1<=len(description)<=80:
        raise ValueError('description must contain 1 to 80 characters')
    return {'asset_id':snapshot['asset_id'], 'expected_generation':snapshot['generation'],
            'before':snapshot['description'], 'after':description,
            'change_required':snapshot['description']!=description}


if __name__=='__main__':
    print(json.dumps(plan(request('/api/devices/r1'),'Aldergate verified uplink'),indent=2))
