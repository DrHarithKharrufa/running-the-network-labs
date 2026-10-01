"""Send exactly one classic-STP BPDU on a disposable lab host's eth1."""
import socket,struct
s=socket.socket(socket.AF_PACKET,socket.SOCK_RAW)
s.bind(('eth1',0))
mac=s.getsockname()[4]
bid=bytes.fromhex('0000020000001299')
bpdu=struct.pack('!HBBB',0,0,0,0)+bid+struct.pack('!I',0)+bid+struct.pack('!HHHHH',0x8001,0,20*256,2*256,15*256)
payload=b'\x42\x42\x03'+bpdu
frame=bytes.fromhex('0180c2000000')+mac+struct.pack('!H',len(payload))+payload
sent=s.send(frame.ljust(60,b'\x00'))
s.close()
print('One lab BPDU sent:',sent,'bytes')
