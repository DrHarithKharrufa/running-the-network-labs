"""Small DNS UDP/TCP and NTP response probes; not protocol conformance tests."""
import socket,struct,sys,json
kind=sys.argv[1];dst='10.109.0.10';source=sys.argv[2] if len(sys.argv)>2 else None
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM if kind=='dns-tcp' else socket.SOCK_DGRAM);s.settimeout(1)
if source:s.bind((source,0))
if kind.startswith('dns'):
 data=struct.pack('!HHHHHH',0x2301,0x0100,1,0,0,0)+b'\x03svc\x03lab\x00'+struct.pack('!HH',1,1)
 if kind=='dns-tcp':
  s.connect((dst,53));s.sendall(struct.pack('!H',len(data))+data)
  def readn(n):
   b=b''
   while len(b)<n:
    part=s.recv(n-len(b))
    if not part:raise EOFError
    b+=part
   return b
  r=readn(struct.unpack('!H',readn(2))[0])
 else:s.sendto(data,(dst,53));r,_=s.recvfrom(4096)
 ident,flags,qd,an,ns,ar=struct.unpack('!HHHHHH',r[:12])
 assert ident==0x2301 and flags&0x8000 and flags&15==0 and an==1 and r[-4:]==socket.inet_aton(dst)
 print(json.dumps({'type':kind,'answers':an,'address':socket.inet_ntoa(r[-4:])}))
else:
 data=bytearray(48);data[0]=0x23;data[40:48]=b'NETBOOK3';s.sendto(data,(dst,123));r,_=s.recvfrom(512)
 assert len(r)>=48 and r[0]&7==4 and r[1]==10 and r[24:32]==data[40:48]
 print(json.dumps({'type':'ntp','stratum':r[1],'scope':'isolated local source; no UTC accuracy claim'}))
