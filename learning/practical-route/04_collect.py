"""Read a real local HTTP service serving simulated device state."""
import json
from common import request, validate_snapshot

if __name__=='__main__':
    result=validate_snapshot(request('/api/devices/r1'))
    print(json.dumps(result,indent=2))
