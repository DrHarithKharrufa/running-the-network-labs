"""Bounded synthetic TCP/UDP echo service for owned isolated workbook hosts."""
import argparse,datetime,ipaddress,json,socket,time
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def family(address):return socket.AF_INET6 if ipaddress.ip_address(address).version==6 else socket.AF_INET
def bounded(sock,deadline,limit):
 remaining=deadline-time.monotonic()
 if remaining<=0:raise socket.timeout('absolute deadline')
 sock.settimeout(min(limit,remaining))
def serve(a):
 typ=socket.SOCK_STREAM if a.transport=='tcp' else socket.SOCK_DGRAM
 with socket.socket(family(a.bind),typ) as s:
  s.bind((a.bind,a.port));s.settimeout(.5)
  if typ==socket.SOCK_STREAM:s.listen(5)
  print(json.dumps({'event':'READY','address':s.getsockname(),'transport':a.transport,'utc':stamp(),'synthetic_service':True}),flush=True)
  deadline=time.monotonic()+a.seconds;done=0
  while done<a.count and time.monotonic()<deadline:
   try:
    bounded(s,deadline,.5)
    if typ==socket.SOCK_STREAM:
     conn,peer=s.accept()
     with conn:
      transaction_deadline=min(deadline,time.monotonic()+1);data=b''
      while len(data)<256 and not data.endswith(b'\n'):
       bounded(conn,transaction_deadline,1)
       chunk=conn.recv(256-len(data))
       if not chunk:break
       data+=chunk
      if not data.endswith(b'\n'):
       print(json.dumps({'event':'REJECT_INCOMPLETE','peer':peer,'bytes':len(data),'utc':stamp()}),flush=True);continue
      bounded(conn,transaction_deadline,1);conn.sendall(data)
    else:data,peer=s.recvfrom(256);s.sendto(data,peer)
    done+=1;print(json.dumps({'event':'ECHO','peer':peer,'bytes':len(data),'utc':stamp()}),flush=True)
   except OSError as e:
    print(json.dumps({'event':'WAIT_OR_REJECT','error':type(e).__name__,'utc':stamp()}),flush=True)
  print(json.dumps({'event':'STOP','transactions':done,'utc':stamp(),'reason':'count or independent controller deadline'}),flush=True)
def probe(a):
 if family(a.source)!=family(a.target):raise ValueError('source/target address families differ')
 typ=socket.SOCK_STREAM if a.transport=='tcp' else socket.SOCK_DGRAM;out=[];deadline=time.monotonic()+a.seconds
 for i in range(a.count):
  payload=(f'{a.label}:{i+1:03}\n').encode('ascii');row={'sequence':i+1,'source_port':a.source_port_base+i,'utc':stamp()}
  if time.monotonic()>=deadline:
   out.append({**row,'echo_matches':False,'decision':'NOT_OFFERED_DEADLINE'});break
  try:
   with socket.socket(family(a.source),typ) as s:
    transaction_deadline=min(deadline,time.monotonic()+a.timeout)
    bounded(s,transaction_deadline,a.timeout);s.bind((a.source,a.source_port_base+i))
    if typ==socket.SOCK_STREAM:
     s.connect((a.target,a.port));bounded(s,transaction_deadline,a.timeout);s.sendall(payload);response=b''
     while len(response)<len(payload):
      bounded(s,transaction_deadline,a.timeout)
      chunk=s.recv(len(payload)-len(response))
      if not chunk:break
      response+=chunk
    else:
     s.connect((a.target,a.port));s.send(payload);bounded(s,transaction_deadline,a.timeout);response=s.recv(256)
    row['echo_matches']=response==payload
  except OSError as e:row.update(echo_matches=False,error=type(e).__name__,detail=str(e))
  out.append(row)
 print(json.dumps({'mode':'BOUNDED_SYNTHETIC_SERVICE_TRIAL','transport':a.transport,'target':a.target,'port':a.port,'results':out,'successes':sum(x['echo_matches'] for x in out),'wire_packet_count_not_asserted':True},indent=2))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['serve','probe']);p.add_argument('--transport',choices=['tcp','udp'],default='tcp');p.add_argument('--bind',default='127.0.0.1');p.add_argument('--source',default='127.0.0.1');p.add_argument('--target',default='127.0.0.1');p.add_argument('--port',type=int,default=8443);p.add_argument('--count',type=int,default=5);p.add_argument('--seconds',type=int,default=30);p.add_argument('--timeout',type=float,default=2);p.add_argument('--source-port-base',type=int,default=40100);p.add_argument('--label',default='WB-OWNED');a=p.parse_args()
 if not 1<=a.count<=100 or not 1<=a.seconds<=300 or not 0<a.timeout<=5 or not 1<=a.port<=65535 or not 1024<=a.source_port_base<=65536-a.count:raise ValueError('invalid bounded port/count/time values')
 if not a.label.isascii() or not 1<=len(a.label)<=64 or not a.label.replace('-','').replace('_','').isalnum():raise ValueError('label must be bounded ASCII alphanumeric/hyphen/underscore')
 (serve if a.action=='serve' else probe)(a)
if __name__=='__main__':main()
