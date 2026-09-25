"""Offline maintenance-window arithmetic; durations are supplied bounds, not measured here."""
from dataclasses import dataclass
import json
import math


def duration(x):
    if type(x) not in (int,float) or not math.isfinite(x) or x < 0:
        raise ValueError('durations must be finite, non-negative minutes')
    return x


@dataclass(frozen=True)
class RecoveryPlan:
    window_minutes: float
    decision_minutes: float
    recovery_minutes: float
    verification_minutes: float
    contingency_minutes: float
    recovery_kind: str = 'rollback'

    def __post_init__(self):
        for v in [self.window_minutes,self.decision_minutes,self.recovery_minutes,
                  self.verification_minutes,self.contingency_minutes]:
            duration(v)
        if self.window_minutes == 0 or self.recovery_minutes == 0 or self.verification_minutes == 0:
            raise ValueError('window, recovery and verification require positive durations')
        if self.recovery_kind not in {'rollback','forward recovery'}:
            raise ValueError('name a tested recovery route; no automatic reversibility assumption')

    @property
    def reserve(self):
        return self.decision_minutes+self.recovery_minutes+self.verification_minutes+self.contingency_minutes

    @property
    def latest_abort(self):
        return self.window_minutes-self.reserve

    def assess(self, elapsed, proposed_stage):
        duration(elapsed); duration(proposed_stage)
        if self.latest_abort < 0:
            return 'DO NOT START'
        if elapsed >= self.latest_abort:
            return 'RECOVERY DECISION NOW'
        if elapsed+proposed_stage > self.latest_abort:
            return 'DO NOT START NEXT STAGE'
        return 'STAGE FITS TIME BUDGET'


def demo():
    plan = RecoveryPlan(120,2,18,12,8)
    return {'scope':'offline arithmetic; timing feasibility is not approval or proof of recovery',
            'reserve_minutes':plan.reserve, 'latest_abort_minutes':plan.latest_abort,
            'elapsed_65_stage_15':plan.assess(65,15),
            'elapsed_65_stage_16':plan.assess(65,16),
            'elapsed_80_stage_1':plan.assess(80,1),
            'naive_abort_at_110_overrun_minutes':110+plan.reserve-plan.window_minutes}


if __name__ == '__main__':
    print(json.dumps(demo(),indent=2))
