"""IPv4 UDP multicast sender/receiver with explicit interface, source filter and sequence tags."""
import socket,struct,time,json,sys,signal
mode,group,interface=sys.argv[1:4];port=5000
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
if mode=='send':
 tag=sys.argv[4];count=int(sys.argv[5]);ttl=int(sys.argv[6]) if len(sys.argv)>6 else 8
 s.bind((interface,0));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_IF,socket.inet_aton(interface));s.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,ttl)
 for n in range(count):s.sendto(json.dumps({'tag':tag,'sequence':n,'sent_monotonic':time.monotonic()}).encode(),(group,port));time.sleep(.02)
 print(json.dumps({'sent':count,'tag':tag,'source':interface,'ttl':ttl}))
else:
 source=sys.argv[4];s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.setsockopt(socket.IPPROTO_IP,49,0);s.bind(('',port))
 if source=='asm':s.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(group)+socket.inet_aton(interface))
 else:s.setsockopt(socket.IPPROTO_IP,39,socket.inet_aton(group)+socket.inet_aton(interface)+socket.inet_aton(source))
 print(json.dumps({'ready':True,'group':group,'filter':source,'interface':interface}),flush=True)
 while True:
  data,peer=s.recvfrom(4096);row=json.loads(data);row.update(received_monotonic=time.monotonic(),peer=peer[0]);print(json.dumps(row),flush=True)
