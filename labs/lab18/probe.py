"""Teaching controller for the isolated Lab 18 topology; not BFD or a NOS SLA."""
import subprocess as sp,time,signal,json

running=True
def stop(*_):
 global running
 running=False
for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,stop)

def route(present):
 args=['ip','route','replace' if present else 'del','203.0.113.0/24','via','192.0.2.2','dev','eth2','metric','10']
 r=sp.run(args,capture_output=True,text=True)
 if r.returncode and not (not present and 'No such process' in r.stderr):raise RuntimeError(r.stderr)

# Start fail-closed; only this script may own the metric-10 service route.
# Probe /32 and its discard fallback are independent of this route.
state=False;route(False);good=bad=0
print(json.dumps({'event':'started','monotonic':time.monotonic(),'primary':False}),flush=True)
try:
 while running:
  started=time.monotonic()
  r=sp.run(['ping','-n','-c','1','-W','1','-I','192.0.2.1','198.19.0.20'],capture_output=True)
  healthy=r.returncode==0
  good=good+1 if healthy else 0;bad=0 if healthy else bad+1
  desired=state
  if not state and good>=3:desired=True
  if state and bad>=2:desired=False
  if desired!=state:
   route(desired);state=desired
   print(json.dumps({'event':'transition','monotonic':time.monotonic(),'primary':state,'consecutive_successes':good,'consecutive_failures':bad}),flush=True)
  # One-second minimum start spacing; process/OS delay can lengthen this.
  time.sleep(max(0,1-(time.monotonic()-started)))
finally:
 route(False)
 print(json.dumps({'event':'stopped','monotonic':time.monotonic(),'primary':False}),flush=True)
