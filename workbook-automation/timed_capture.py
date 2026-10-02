"""OPS-11: finite local tcpdump capture, previewed unless --execute is explicit."""
import argparse,json,re,subprocess,ipaddress,time
from pathlib import Path
def command(interface,out,count,host='192.0.2.2'):
 if re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}',interface) is None:raise ValueError('invalid owned interface')
 if not 1<=count<=100:raise ValueError('bounded count must be 1..100')
 address=ipaddress.ip_address(host);proto='icmp6' if address.version==6 else 'icmp'
 return ['tcpdump','-i',interface,'-nn','-s','160','-c',str(count),'-w',str(out),proto+' and host '+str(address)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--interface',required=True);p.add_argument('--host',default='192.0.2.2');p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=10);p.add_argument('--seconds',type=int,default=10);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not 1<=a.seconds<=60:raise ValueError('stop bound must be 1..60 seconds')
 cmd=command(a.interface,a.out,a.count,a.host)
 if not a.execute:print(json.dumps({'mode':'PREVIEW','argv':cmd,'stop_request_seconds':a.seconds,'termination_grace_seconds':3,'device_execution':False},indent=2));return
 if a.out.exists():raise ValueError('refuse to overwrite an existing capture')
 # Invoke inside the declared isolated lab namespace/VM, not a shared host.
 started=time.monotonic();proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL)
 try:result=proc.wait(timeout=a.seconds);reason='packet-count or process exit'
 except subprocess.TimeoutExpired:
  proc.terminate();reason='controller time bound'
  try:result=proc.wait(timeout=3)
  except subprocess.TimeoutExpired:proc.kill();result=proc.wait();reason+='; forced stop'
 print(json.dumps({'reason':reason,'exit_code':result,'elapsed_seconds':time.monotonic()-started,'stop_request_seconds':a.seconds,'termination_grace_seconds':3,'out':str(a.out),'scope':'local capture only; inspect truncation and independent wire witness'}))
if __name__=='__main__':main()
