# Worked guidance

Attempt the tasks before reading these. All observations below are expected results from the supplied teaching inputs, not a report about a real enterprise.

**P1.** Inside the loop use `print(f"{device['asset_id']} -> {device['management_ip']}")`. For filtering, put that statement under `if device['owner'] == 'branch-team':`. There are two matching rows initially; changing r3's owner gives three. The double outer quotes permit single quotes for dictionary keys inside the f-string.

**P2.** `if not row['owner'].strip(): raise ValueError('missing owner')`. `strip()` removes leading/trailing whitespace; `not` treats the resulting empty string as false. Test both `''` and `'   '`. Add duplicate detection by keeping a set and checking membership before adding a value. The complete function in `02_addresses.py` demonstrates the order. `192.0.2.11` belongs to `192.0.2.0/24`, but not `198.51.100.0/24`. The IPv6 form can use `2001:db8:1::11` in `2001:db8:1::/64`.

**P3.** Four errors divided by 100 packets is 0.04, or 4%. When packets is zero, return `None`; serialisation writes `null`. Use interval deltas and reset handling before interpreting cumulative counters as an operational error rate. Deleting eth2 must raise an error because its expected observation is missing; it must not remove the port from the report and call the rest a success.

**P5.** Compare `snapshot['description'] != desired`. Return the original description, desired description and observed generation; do not call the write API inside the planner. A function returning a plan is easy to test with dictionaries. Reject an empty desired description before generating a plan, because validation belongs before remote mutation.

**P7.** In two terminals, collect r1 at generation N. Make a first PUT with `expected_generation: N`; it succeeds and advances to N+1. The second PUT using N returns 409 and does not overwrite the first. Replacing N with N+1 without reviewing the new state would authorise a different change from the one you inspected. The lost-reply test intentionally mutates the simulated device, then raises TimeoutError. Read-back finds the new description but the client retains `UNKNOWN_WRITE`; the policy requires deliberate reconciliation before a later action. Restoration is a separate write and can itself fail or conflict.

**P8.** Save one dictionary and reuse it exactly:

```python
import time, uuid
from common import request
event = {'event_id': uuid.uuid4().hex, 'sensor_id': 'sensor-r1-eth2',
         'status': 'Down', 'observed_at': int(time.time()),
         'sequence': time.time_ns() // 1_000_000}
first = request('/events', 'POST', event)
second = request('/events', 'POST', event)
assert first['case_id'] == second['case_id']
assert second['duplicate'] is True
```

Save the event to JSON before stopping the server. Reload that exact file after restart; do not regenerate the timestamp or ID. A payload fingerprint detects the same ID reused with different content. This local transaction prevents duplicate *local case rows*; it makes no claim about exactly-once effects in an external ticket service. A separate source event after recovery needs its own identity and ordering information.
