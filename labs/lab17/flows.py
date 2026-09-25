"""Bounded UDP echo and raw egress observation; not a throughput benchmark."""
import argparse,socket,struct,time,signal,json
from pathlib import Path

def server():
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('10.0.2.10',9000));print('READY',flush=True)
 while True:
  data,addr=s.recvfrom(256);s.sendto(data,addr)

def client(count,samples):
 delivered=0
 for port in range(20000,20000+count):
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
   s.settimeout(2);s.bind(('10.0.1.10',port))
   for i in range(samples):
    data=f'{port}/{i}'.encode();s.sendto(data,('10.0.2.10',9000))
    reply,peer=s.recvfrom(256)
    if reply!=data or peer!=('10.0.2.10',9000):raise RuntimeError('Unexpected reply')
    delivered+=1
 print(json.dumps({'flows':count,'samples_per_flow':samples,'echoes':delivered}),flush=True)

def observe(out):
 running=True
 def stop(*args):
  nonlocal running
  running=False
 signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
 sock=socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3));sock.settimeout(.2)
 ports={f'eth{i}':{} for i in range(2,6)}
 # Classic pcap, Ethernet, captured prefix only; independent decoder can inspect it.
 with out.with_suffix('.pcap').open('wb') as cap:
  cap.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,96,1))
  print('READY',flush=True)
  while running:
   try:data,addr=sock.recvfrom(65535)
   except socket.timeout:continue
   iface,proto,kind=addr[:3]
   if iface not in ports or kind!=socket.PACKET_OUTGOING or len(data)<42:continue
   if data[12:14]!=b'\x08\x00' or data[23]!=17:continue
   ihl=(data[14]&15)*4;start=14+ihl
   src,dst=struct.unpack('!HH',data[start:start+4])
   if dst!=9000 or not 20000<=src<21024:continue
   ports[iface][str(src)]=ports[iface].get(str(src),0)+1
   now=time.time();sec=int(now);packet=data[:96]
   cap.write(struct.pack('<IIII',sec,int((now-sec)*1e6),len(packet),len(data))+packet)
 result={'ports':ports,'flow_counts':{n:len(p) for n,p in ports.items()},'packet_counts':{n:sum(p.values()) for n,p in ports.items()}}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['flow_counts']),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['server','client','observe']);p.add_argument('--flows',type=int,default=1024);p.add_argument('--samples',type=int,default=4);p.add_argument('--output',type=Path,default=Path('/tmp/lab17-observation.json'))
 a=p.parse_args()
 if not 1<=a.flows<=1024 or not 1<=a.samples<=256:p.error('bounded ranges: flows 1..1024, samples 1..256')
 if a.mode=='server':server()
 elif a.mode=='client':client(a.flows,a.samples)
 else:observe(a.output)
