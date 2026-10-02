"""Finite isolated HTTPS listener/probe; verified TLS, no files or network devices."""
import argparse,datetime,ipaddress,json,socket,ssl,time
def emit(**row):print(json.dumps(row),flush=True)
def bounded(sock,deadline):
 remaining=deadline-time.monotonic()
 if remaining<=0:raise TimeoutError('absolute transaction/controller deadline')
 sock.settimeout(remaining)
def receive_headers(sock,deadline):
 data=b''
 while b'\r\n\r\n' not in data and len(data)<4096:
  bounded(sock,deadline);part=sock.recv(min(1024,4096-len(data)))
  if not part:break
  data+=part
 if b'\r\n\r\n' not in data:raise ValueError('incomplete or oversized HTTP headers')
 return data
def serve(a):
 context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(a.cert,a.key)
 with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listener:
  listener.bind((a.bind,a.port));listener.listen(5)
  emit(event='READY',address=listener.getsockname(),protocol='HTTPS',synthetic_service=True)
  deadline=time.monotonic()+a.seconds;success=0;attempts=0
  while success<a.count and time.monotonic()<deadline:
   try:
    listener.settimeout(min(.5,deadline-time.monotonic()));raw,peer=listener.accept();attempts+=1
    transaction_deadline=min(deadline,time.monotonic()+a.timeout)
    with raw:
     bounded(raw,transaction_deadline)
     with context.wrap_socket(raw,server_side=True) as conn:
      request=receive_headers(conn,transaction_deadline)
      if not request.startswith(b'GET /wb HTTP/1.1\r\n'):raise ValueError('only the fixed /wb request is accepted')
      body=b'WB-HTTPS-OK\n';response=b'HTTP/1.1 200 OK\r\nContent-Length: 12\r\nConnection: close\r\nContent-Type: text/plain\r\n\r\n'+body
      bounded(conn,transaction_deadline);conn.sendall(response);success+=1
      emit(event='HTTPS_RESPONSE',peer=peer,tls=conn.version(),status=200)
   except socket.timeout:continue
   except (OSError,ValueError) as e:emit(event='REJECT',error=type(e).__name__)
  emit(event='STOP',responses=success,accepted_connections=attempts)
def probe(a):
 context=ssl.create_default_context(cafile=a.ca);context.minimum_version=ssl.TLSVersion.TLSv1_2
 deadline=time.monotonic()+a.seconds;results=[]
 for i in range(a.count):
  row={'sequence':i+1,'source_port':a.source_port_base+i,'success':False}
  if time.monotonic()>=deadline:
   results.append({**row,'decision':'NOT_OFFERED_DEADLINE'});break
  try:
   transaction_deadline=min(deadline,time.monotonic()+a.timeout)
   with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as raw:
    raw.bind((a.source,a.source_port_base+i));bounded(raw,transaction_deadline);raw.connect((a.target,a.port))
    bounded(raw,transaction_deadline)
    with context.wrap_socket(raw,server_hostname=a.server_name) as conn:
     bounded(conn,transaction_deadline);conn.sendall(('GET /wb HTTP/1.1\r\nHost: '+a.server_name+'\r\nConnection: close\r\n\r\n').encode('ascii'))
     data=receive_headers(conn,transaction_deadline);head,body=data.split(b'\r\n\r\n',1)
     while len(body)<12:
      bounded(conn,transaction_deadline);part=conn.recv(12-len(body))
      if not part:break
      body+=part
     row.update(success=head.startswith(b'HTTP/1.1 200 OK\r\n') and body==b'WB-HTTPS-OK\n',tls=conn.version(),verified_peer=True)
  except (OSError,ValueError) as e:row.update(error=type(e).__name__,detail=str(e))
  results.append(row)
 emit(mode='BOUNDED_REAL_HTTPS_FIXTURE',results=results,successes=sum(x['success'] for x in results),vendor_device_execution=False)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['serve','probe']);p.add_argument('--bind',default='127.0.0.1');p.add_argument('--source',default='127.0.0.1');p.add_argument('--target',default='127.0.0.1');p.add_argument('--port',type=int,default=443);p.add_argument('--count',type=int,default=5);p.add_argument('--seconds',type=int,default=30);p.add_argument('--timeout',type=float,default=2);p.add_argument('--source-port-base',type=int,default=40500);p.add_argument('--cert');p.add_argument('--key');p.add_argument('--ca');p.add_argument('--server-name');a=p.parse_args()
 if not 1<=a.count<=100 or not 1<=a.seconds<=300 or not 0<a.timeout<=5 or not 1<=a.port<=65535 or not 1024<=a.source_port_base<=65536-a.count:raise ValueError('invalid bounded values')
 for value in [a.bind,a.source,a.target]:
  if ipaddress.ip_address(value).version!=4:raise ValueError('this declared fixture uses IPv4')
 if a.action=='serve' and not(a.cert and a.key):raise ValueError('server certificate and protected key required')
 if a.action=='probe' and not(a.ca and a.server_name):raise ValueError('trusted CA and exact certificate DNS/IP identity required')
 if a.server_name and (not a.server_name.isascii() or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-:' for c in a.server_name)):raise ValueError('invalid server identity')
 (serve if a.action=='serve' else probe)(a)
if __name__=='__main__':main()
