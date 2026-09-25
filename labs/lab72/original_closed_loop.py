#!/usr/bin/env python3
"""
Lab 72.1 -- a closed loop with interlocks, and a runaway it stops.

Chapter 72: observe, decide, act, VERIFY -- plus rate limit, circuit breaker and
kill switch (sec 6). This simulates a loop reacting to an event, and shows the
circuit breaker tripping when actions keep failing their verify -- turning a
machine-speed catastrophe into a safe stop.

    python3 closed_loop.py
"""

class Interlocks:
    def __init__(self, rate_limit, breaker_threshold):
        self.rate_limit = rate_limit          # max actions per window
        self.breaker_threshold = breaker_threshold
        self.actions_this_window = 0
        self.consecutive_failures = 0
        self.tripped = False

    def allow(self):
        if self.tripped:
            return False, "circuit breaker TRIPPED -- loop halted"
        if self.actions_this_window >= self.rate_limit:
            return False, "rate limit reached -- deferring"
        return True, "ok"

    def record(self, verified_ok):
        self.actions_this_window += 1
        if verified_ok:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.breaker_threshold:
                self.tripped = True

def run_loop(events, act_succeeds, interlocks):
    """observe(event) -> decide -> act -> verify; interlocks bound the damage."""
    for i, ev in enumerate(events, 1):
        ok, why = interlocks.allow()
        if not ok:
            print(f"  event {i}: BLOCKED by interlock -- {why}")
            if interlocks.tripped:
                print("  --> loop stopped acting. A human is paged (kill switch ready).")
                break
            continue
        verified = act_succeeds(ev)           # act, then VERIFY the effect
        interlocks.record(verified)
        status = "verified OK" if verified else "verify FAILED -> rollback"
        print(f"  event {i}: acted, {status}  "
              f"(consec fails={interlocks.consecutive_failures})")

if __name__ == "__main__":
    print("Healthy loop: actions succeed and verify (rate limit 5/window):\n")
    run_loop(range(4), act_succeeds=lambda e: True,
             interlocks=Interlocks(rate_limit=5, breaker_threshold=3))

    print("\nRunaway loop: a bad signal makes every action fail its verify:\n")
    run_loop(range(10), act_succeeds=lambda e: False,
             interlocks=Interlocks(rate_limit=50, breaker_threshold=3))
    print("\nThe breaker stopped the loop after 3 failed verifies instead of")
    print("'fixing' hundreds of devices wrongly at machine speed (sec 5, sec 6).")
