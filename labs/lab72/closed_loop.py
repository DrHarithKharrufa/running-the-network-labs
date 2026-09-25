#!/usr/bin/env python3
"""One-process, in-memory closed-loop teaching model; no bus, NOS or external alerts."""
from collections import deque
from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
import runpy
from threading import RLock
import time

class Conflict(Exception):
    pass

@dataclass(frozen=True)
class Event:
    event_id: str
    produced_at: float
    expected_version: int
    producer: str = "monitor-a"
    target: str = "test-service"
    desired: str = "mitigated"

@dataclass
class Device:
    value: str = "baseline"
    version: int = 0
    healthy: bool = True
    readable: bool = True
    writes: int = 0

    def apply(self, expected_version, value, fault="ok"):
        if expected_version != self.version:
            raise Conflict("version changed")
        if fault == "reject":
            raise PermissionError("simulated pre-write rejection")
        self.writes += 1
        if fault == "noop":
            return
        self.value = value
        self.version += 1
        if fault == "bad-health":
            self.healthy = False
        if fault == "lost-reply":
            raise TimeoutError("simulated reply lost after write")

    def observe(self):
        if not self.readable:
            raise TimeoutError("observation unavailable")
        return {"value": self.value, "version": self.version, "healthy": self.healthy}

    def restore(self, expected_version, baseline):
        if self.version != expected_version:
            raise Conflict("newer state must not be overwritten")
        self.value, self.healthy = baseline["value"], baseline["healthy"]
        self.version += 1
        self.writes += 1

class MemoryNotifications:
    """Local adapter only. No email, pager, webhook or external delivery."""
    def __init__(self): self.records = []
    def emit(self, record): self.records.append(dict(record))

class Interlocks:
    def __init__(self, rate_limit=3, window=60., breaker_threshold=2,
                 cooldown=30., monotonic=time.monotonic):
        if any(type(v) is not int or v < 1 for v in [rate_limit, breaker_threshold]):
            raise ValueError("limits must be positive integers")
        if any(type(v) not in (int,float) or not math.isfinite(v) or v <= 0 for v in [window,cooldown]):
            raise ValueError("durations must be positive and finite")
        self.rate_limit,self.window,self.threshold,self.cooldown=rate_limit,window,breaker_threshold,cooldown
        self.clock=monotonic;self.starts=deque();self.failures=0;self.tripped_at=None
        self.killed=False;self.available=True;self.epoch=0;self.lock=RLock()

    def reserve(self):
        with self.lock:
            now=self.clock()
            while self.starts and now-self.starts[0]>=self.window:self.starts.popleft()
            if not self.available or self.killed or self.tripped_at is not None:return None
            if len(self.starts)>=self.rate_limit:return None
            self.starts.append(now)  # reserve before acting, including uncertain attempts
            return self.epoch

    def still_allowed(self, epoch):
        with self.lock:
            return self.available and not self.killed and self.tripped_at is None and epoch==self.epoch

    def record(self, failed):
        with self.lock:
            self.failures=self.failures+1 if failed else 0
            if self.failures>=self.threshold:
                self.tripped_at=self.clock();self.epoch+=1

    def kill(self):
        with self.lock:self.killed=True;self.epoch+=1

    def reset(self, *, manual=False, observed_healthy=False):
        with self.lock:
            if not manual or not observed_healthy or not self.available:return False
            if self.tripped_at is not None and self.clock()-self.tripped_at<self.cooldown:return False
            self.killed=False;self.tripped_at=None;self.failures=0;self.epoch+=1
            return True  # rate-window reservations are deliberately not cleared

class Loop:
    def __init__(self, device, interlocks=None, notifications=None, wall_clock=time.time):
        self.device=device;self.guards=interlocks or Interlocks()
        self.notifications=notifications or MemoryNotifications();self.clock=wall_clock
        self.results={};self.lock=RLock();self.notification_failed=False

    def notify(self, record):
        try:self.notifications.emit(record)
        except Exception:
            self.notification_failed=True;self.guards.kill()

    def process(self, event, *, fault="ok", before_write=None, after_write=None):
        # Serialises this one process only. It is not a distributed lock/lease.
        with self.lock:
            if fault not in {"ok","reject","noop","bad-health","lost-reply"}:raise ValueError("unknown fault")
            if not isinstance(event,Event):raise ValueError("Event required")
            result={"event":str(event.event_id),"status":"REJECTED","history":[],"observation":None,"received_at":self.clock()}
            valid=(type(event.event_id) is str and bool(event.event_id) and
                   type(event.expected_version) is int and event.expected_version>=0 and
                   type(event.produced_at) in (int,float) and math.isfinite(event.produced_at) and
                   event.producer=="monitor-a" and event.target=="test-service" and event.desired=="mitigated")
            if not valid:return dict(result,reason="schema or fixture provenance rejected")
            key=(event.producer,event.event_id)
            if key in self.results:
                prior_event,prior_result=self.results[key]
                if event!=prior_event:return dict(result,reason="event ID collision")
                return dict(prior_result,duplicate=True)
            if len(self.results)>=1000:
                self.guards.kill();return dict(result,reason="teaching deduplication capacity exhausted")
            age=self.clock()-event.produced_at
            if age>30 or age < -2:return dict(result,reason="stale/future event")
            # Producer allow-list is fixture validation; cryptographic authentication is absent.
            try:baseline=self.device.observe()
            except TimeoutError:return dict(result,status="UNKNOWN",reason="no baseline; no write attempted")
            if event.expected_version!=baseline['version']:return dict(result,reason="stale resource version")
            epoch=self.guards.reserve()
            if epoch is None:return dict(result,status="BLOCKED",reason="interlock or rate budget")
            self.results[key]=(event,result)
            if before_write:before_write()
            if not self.guards.still_allowed(epoch):
                result.update(status="CANCELLED_BEFORE_WRITE");return dict(result)
            if not -2 <= self.clock()-event.produced_at <= 30:
                result.update(status="EXPIRED_BEFORE_WRITE");return dict(result)
            uncertain=False
            try:
                self.device.apply(event.expected_version,event.desired,fault)
                result['history'].append('APPLY_ACKNOWLEDGED')
            except TimeoutError:
                uncertain=True;result['history'].append('UNKNOWN_WRITE')
            except (PermissionError,Conflict) as exc:
                result['history'].append(type(exc).__name__)
                result.update(status='REJECTED');self.guards.record(True);self.notify(result);return dict(result)
            if after_write:after_write()
            try:
                observation=self.device.observe();result['observation']=observation
            except TimeoutError:
                result.update(status='UNKNOWN');self.guards.kill();self.guards.record(True);self.notify(result);return dict(result)
            # A kill switch prevents further writes, including automatic compensation.
            if not self.guards.still_allowed(epoch):
                result.update(status='STOPPED_RECONCILIATION_REQUIRED');self.notify(result);return dict(result)
            owned_version=baseline['version']+1
            verified=(observation['value']==event.desired and observation['healthy'] and observation['version']==owned_version)
            if verified:
                result.update(status='RECONCILED_APPLIED' if uncertain else 'VERIFIED_SCOPE')
            else:
                try:
                    self.device.restore(owned_version,baseline)
                    restored=self.device.observe();result['observation']=restored
                    result.update(status='ROLLED_BACK_SCOPE' if restored['value']==baseline['value'] and restored['healthy']==baseline['healthy'] else 'UNKNOWN')
                except Conflict:result.update(status='CONFLICT_REQUIRES_REVIEW')
                except TimeoutError:result.update(status='UNKNOWN');self.guards.kill()
            self.guards.record(uncertain or not verified)
            result['history'].append(result['status']);self.notify(result)
            return dict(result)

def demonstration():
    device=Device();sink=MemoryNotifications();loop=Loop(device,notifications=sink)
    e=Event('e1',time.time(),0)
    results=[loop.process(e,fault='bad-health'),loop.process(e)]
    results.append(loop.process(Event('e2',time.time(),device.version),fault='bad-health'))
    results.append(loop.process(Event('e3',time.time(),device.version)))
    return {'scope':__doc__,'results':results,'device':device.observe(),
            'writes':device.writes,'breaker_tripped':loop.guards.tripped_at is not None,
            'local_notifications':sink.records,'external_notifications_sent':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--demo-original',action='store_true');args=parser.parse_args()
    if args.demo_original:
        print('HISTORICAL FLAWED DEMO: verification, rollback and paging claims were not implemented.')
        runpy.run_path(str(Path(__file__).with_name('original_closed_loop.py')),run_name='__main__')
    else:print(json.dumps(demonstration(),indent=2))
