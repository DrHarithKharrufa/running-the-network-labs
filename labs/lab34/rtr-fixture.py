"""Isolated RTR v1 fixture, not a relying-party validator or public RPKI service.

Serves explicitly synthetic IPv4 prefix/origin records from a local JSON file.
No certificates, ROAs, repository retrieval or signatures are validated.
Only the Reset/Serial exchanges needed by the local lab are implemented.
Bind to namespace loopback. Never use as a production cache.
"""
import socket,socketserver,struct,json,sys,ipaddress,time
from pathlib import Path
FILE=Path(sys.argv[1]);PORT=int(sys.argv[2]) if len(sys.argv)>2 else 3323
def header(kind,session,length):return struct.pack('!BBHI',1,kind,session,length)
def readn(sock,n):
 data=b''
 while len(data)<n:
  part=sock.recv(n-len(data))
  if not part:raise EOFError
  data+=part
 return data
class Handler(socketserver.BaseRequestHandler):
 def handle(self):
  try:
   while True:
    raw=readn(self.request,8);version,kind,sid,length=struct.unpack('!BBHI',raw)
    if length<8 or length>4096:raise ValueError('Unsupported PDU length')
    body=readn(self.request,length-8)
    if version!=1:raise ValueError('Fixture only supports RTRv1')
    data=json.loads(FILE.read_text());serial=data['serial'];session=data.get('session',22)
    print(json.dumps({'time':time.time(),'received_type':kind,'serial':serial,'session':sid}),flush=True)
    if kind==2:
     payload=header(3,session,8)
     for prefix,maxlen,asn in data['records']:
      net=ipaddress.IPv4Network(prefix)
      payload+=header(4,0,20)+struct.pack('!BBBB4sI',1,net.prefixlen,maxlen,0,net.network_address.packed,asn)
     payload+=header(7,session,24)+struct.pack('!IIII',serial,1,1,600)
     self.request.sendall(payload)
    elif kind==1:
     requested=struct.unpack('!I',body)[0]
     if sid!=session or requested!=serial:self.request.sendall(header(8,0,8))
     else:self.request.sendall(header(3,session,8)+header(7,session,24)+struct.pack('!IIII',serial,1,1,600))
    else:raise ValueError('Unsupported query type '+str(kind))
  except (EOFError,ConnectionError):pass
  except Exception as exc:print(json.dumps({'error':repr(exc)}),flush=True)
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
with Server(('127.0.0.1',PORT),Handler) as server:
 print('READY',flush=True);server.serve_forever()
