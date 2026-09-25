from concurrent.futures import ThreadPoolExecutor
import unittest
from closed_loop import Device, Event, Interlocks, Loop, MemoryNotifications

class Clock:
    def __init__(self):self.value=100.
    def __call__(self):return self.value

class Tests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.device=Device();self.guards=Interlocks(monotonic=self.clock)
        self.sink=MemoryNotifications();self.loop=Loop(self.device,self.guards,self.sink,self.clock)
    def event(self,name='e1',**kw):
        return Event(name,kw.pop('produced_at',self.clock()),kw.pop('expected_version',self.device.version),**kw)
    def test_independent_read_detects_no_effect(self):
        r=self.loop.process(self.event(),fault='noop');self.assertNotEqual(r['status'],'VERIFIED_SCOPE');self.assertEqual(self.device.value,'baseline')
    def test_verified_state_and_notification(self):
        r=self.loop.process(self.event());self.assertEqual(r['status'],'VERIFIED_SCOPE');self.assertEqual(r['observation']['value'],'mitigated');self.assertEqual(len(self.sink.records),1)
    def test_actual_rollback_and_observation(self):
        r=self.loop.process(self.event(),fault='bad-health');self.assertEqual(r['status'],'ROLLED_BACK_SCOPE');self.assertEqual(self.device.value,'baseline');self.assertTrue(self.device.healthy);self.assertEqual(self.device.writes,2)
    def test_duplicate_does_not_act_again(self):
        e=self.event();self.loop.process(e);r=self.loop.process(e);self.assertTrue(r['duplicate']);self.assertEqual(self.device.writes,1)
    def test_duplicate_id_collision(self):
        self.loop.process(self.event());r=self.loop.process(self.event(expected_version=1));self.assertEqual(r['reason'],'event ID collision');self.assertEqual(self.device.writes,1)
    def test_stale_and_future_events(self):
        for timestamp in [69.,103.]:
            with self.subTest(timestamp=timestamp):self.assertEqual(self.loop.process(self.event(produced_at=timestamp))['reason'],'stale/future event')
        self.assertEqual(self.device.writes,0)
    def test_stale_resource_version(self):
        self.device.version=4;r=self.loop.process(self.event(expected_version=0));self.assertEqual(r['reason'],'stale resource version');self.assertEqual(self.device.writes,0)
    def test_schema_and_fixture_provenance(self):
        for kwargs in [{'producer':'outsider'},{'target':'production'},{'expected_version':True},{'produced_at':float('nan')},{'desired':'shutdown'}]:
            with self.subTest(kwargs=kwargs):self.assertEqual(self.loop.process(self.event(**kwargs))['status'],'REJECTED')
        self.assertEqual(self.device.writes,0)
    def test_rate_window_actually_expires(self):
        guard=Interlocks(rate_limit=1,monotonic=self.clock);self.assertIsNotNone(guard.reserve());self.assertIsNone(guard.reserve())
        self.clock.value+=59;self.assertIsNone(guard.reserve());self.clock.value+=1;self.assertIsNotNone(guard.reserve())
    def test_shared_process_budget_is_atomic(self):
        with ThreadPoolExecutor(max_workers=8) as executor:tokens=list(executor.map(lambda _:self.guards.reserve(),range(20)))
        self.assertEqual(sum(t is not None for t in tokens),3)
    def test_breaker_and_manual_recovery(self):
        for name in ['e1','e2']:self.loop.process(self.event(name),fault='bad-health')
        self.assertIsNotNone(self.guards.tripped_at);self.assertEqual(self.loop.process(self.event('e3'))['status'],'BLOCKED')
        self.assertFalse(self.guards.reset(manual=True,observed_healthy=True));self.clock.value+=31
        self.assertFalse(self.guards.reset(observed_healthy=True));self.assertTrue(self.guards.reset(manual=True,observed_healthy=True))
        self.assertEqual(self.loop.process(self.event('e4'))['status'],'VERIFIED_SCOPE')
    def test_reset_does_not_erase_rate_budget(self):
        for _ in range(3):self.guards.reserve()
        self.guards.kill();self.assertTrue(self.guards.reset(manual=True,observed_healthy=True));self.assertIsNone(self.guards.reserve())
    def test_kill_before_admission(self):
        self.guards.kill();self.assertEqual(self.loop.process(self.event())['status'],'BLOCKED');self.assertEqual(self.device.writes,0)
    def test_kill_reserved_work_before_write(self):
        r=self.loop.process(self.event(),before_write=self.guards.kill);self.assertEqual(r['status'],'CANCELLED_BEFORE_WRITE');self.assertEqual(self.device.writes,0)
    def test_queued_event_expires_before_write(self):
        r=self.loop.process(self.event(),before_write=lambda:setattr(self.clock,'value',140.));self.assertEqual(r['status'],'EXPIRED_BEFORE_WRITE');self.assertEqual(self.device.writes,0)
    def test_kill_after_write_does_not_claim_cancellation(self):
        r=self.loop.process(self.event(),after_write=self.guards.kill);self.assertEqual(r['status'],'STOPPED_RECONCILIATION_REQUIRED');self.assertEqual(self.device.value,'mitigated');self.assertEqual(self.device.writes,1)
    def test_uncertain_write_reconciles_without_retry(self):
        r=self.loop.process(self.event(),fault='lost-reply');self.assertEqual(r['status'],'RECONCILED_APPLIED');self.assertIn('UNKNOWN_WRITE',r['history']);self.assertEqual(self.device.writes,1)
    def test_unknown_observation_halts(self):
        r=self.loop.process(self.event(),fault='lost-reply',after_write=lambda:setattr(self.device,'readable',False));self.assertEqual(r['status'],'UNKNOWN');self.assertTrue(self.guards.killed);self.assertEqual(self.device.value,'mitigated')
    def test_unavailable_baseline_prevents_write(self):
        self.device.readable=False;r=self.loop.process(self.event());self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(self.device.writes,0)
    def test_rollback_cannot_overwrite_newer_change(self):
        def concurrent_change():self.device.value='newer-approved';self.device.version+=1
        r=self.loop.process(self.event(),fault='bad-health',after_write=concurrent_change)
        self.assertEqual(r['status'],'CONFLICT_REQUIRES_REVIEW');self.assertEqual(self.device.value,'newer-approved');self.assertEqual(self.device.writes,1)
    def test_controls_unavailable_fail_closed(self):
        self.guards.available=False;self.assertEqual(self.loop.process(self.event())['status'],'BLOCKED');self.assertEqual(self.device.writes,0)
    def test_notification_failure_halts_future_work(self):
        class FailedSink:
            def emit(self,record):raise OSError('local sink failed')
        self.loop.notifications=FailedSink();self.loop.process(self.event());self.assertTrue(self.loop.notification_failed);self.assertTrue(self.guards.killed)
    def test_unsupported_limits_and_faults(self):
        for kwargs in [{'rate_limit':True},{'window':0},{'cooldown':float('nan')},{'breaker_threshold':-1}]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):Interlocks(**kwargs)
        with self.assertRaises(ValueError):self.loop.process(self.event(),fault='invented')

if __name__=='__main__':unittest.main(verbosity=2)
