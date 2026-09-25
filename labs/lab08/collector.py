"""Small UDP teaching collector: receipt is not end-to-end delivery assurance."""
import socket,sys,json,time
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('10.10.14.10',514))
with open(sys.argv[1],'a',encoding='utf-8',buffering=1) as out:
 while True:
  data,peer=s.recvfrom(4096)
  out.write(json.dumps({'received_unix':time.time(),'peer':peer,'message':data.decode('utf-8',errors='replace')})+'\n')
