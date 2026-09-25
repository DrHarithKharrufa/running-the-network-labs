"""Finite, marked Ethernet experiment for the isolated supplied lab only."""
import socket,sys,struct,time,json
mode,interface,token=sys.argv[1:4]
if not token.startswith('NBK-LAB11-') or len(token)>64:raise SystemExit('Use a short NBK-LAB11- token')
marker=token.encode('ascii')
s=socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3));s.bind((interface,0))
if mode=='send':
 tags=[int(x) for x in sys.argv[4:]]
 if len(tags)>2 or any(x not in [1,110,120] for x in tags):raise SystemExit('Only lab tag values permitted')
 src=s.getsockname()[4]
 frame=b'\xff'*6+src+b''.join(struct.pack('!HH',0x8100,v) for v in tags)+struct.pack('!H',0x88b5)+marker
 frame=frame.ljust(60,b'\0')
 for _ in range(3):s.send(frame);time.sleep(.05)
 print(json.dumps({'submitted_frames':3,'tags':tags,'token':token,'claim':'submission only, inspect receiver'}))
elif mode=='receive':
 deadline=time.monotonic()+3;frames=[];s.settimeout(.2)
 print('READY',flush=True)
 while time.monotonic()<deadline:
  try:data,peer=s.recvfrom(2048)
  except socket.timeout:continue
  if peer[2]!=socket.PACKET_OUTGOING and marker in data:
   frames.append(data.hex())
 print(json.dumps({'token':token,'received_frames':len(frames),'frame_hex':frames}))
else:raise SystemExit('usage: frame_probe.py send|receive IFACE NBK-LAB11-token [OUTER [INNER]]')
