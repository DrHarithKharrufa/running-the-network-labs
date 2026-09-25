"""Send a bounded experimental EtherType frame inside an isolated lab node."""
import argparse,socket,time
p=argparse.ArgumentParser();p.add_argument('interface');p.add_argument('destination');p.add_argument('tag');p.add_argument('--count',type=int,default=5);a=p.parse_args()
assert 1<=a.count<=128 and 1<=len(a.tag.encode())<=40
dst=bytes.fromhex(a.destination.replace(':',''));assert len(dst)==6
s=socket.socket(socket.AF_PACKET,socket.SOCK_RAW);s.bind((a.interface,0));src=s.getsockname()[4]
frame=(dst+src+b'\x88\xb5'+a.tag.encode()).ljust(100,b'X')
for _ in range(a.count):s.send(frame);time.sleep(.05)
