"""Finite single-session echo: observe gaps without reconnecting silently."""
import socket,time,json,sys
if len(sys.argv)!=2 or sys.argv[1] not in ('server','client'):
    raise SystemExit('Usage: tcp-echo.py server|client')
if sys.argv[1]=='server':
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        listener.settimeout(30)
        listener.bind(('198.51.100.10',1313));listener.listen(1)
        print('LISTENING',flush=True)
        connection,_=listener.accept()
        with connection:
            connection.settimeout(12)
            deadline=time.monotonic()+75
            while time.monotonic()<deadline:
                data=connection.recv(64)
                if not data:break
                connection.sendall(data)
else:
    with socket.create_connection(('198.51.100.10',1313),3) as connection:
        connection.settimeout(10)
        print('CONNECTED',flush=True)
        start=time.monotonic();sequence=0
        while time.monotonic()-start<60:
            sequence+=1;sent=time.monotonic();message=('%08d'%sequence).encode()
            connection.sendall(message);data=b''
            while len(data)<len(message):
                part=connection.recv(len(message)-len(data))
                if not part:raise RuntimeError('Connection closed before full echo')
                data+=part
            if data!=message:raise RuntimeError('Incorrect echo')
            print(json.dumps({'seq':sequence,'since_start':sent-start,'round_trip_seconds':time.monotonic()-sent}),flush=True)
            time.sleep(.1)
        print('SESSION_COMPLETED',flush=True)
