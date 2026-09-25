#!/usr/bin/env python3
"""Bounded IPv4 UDP generator/receiver; not congestion controlled.

Rates count UDP payload only. Delay requires sender and receiver to share
the same kernel monotonic clock (this namespace/container lab).
"""
import argparse,socket,time,struct,json,heapq,selectors,math
MAGIC=b'NBQ31v1!'
HEADER=struct.Struct('!8sIQ')

def positive(value):
    n=float(value)
    if not math.isfinite(n) or n<=0: raise argparse.ArgumentTypeError('must be finite and positive')
    return n

def send(a):
    q=[];rows={};start=time.monotonic();end=start+a.seconds
    for i,spec in enumerate(a.flow):
        name,port,tos,rate=spec.split(':');port=int(port);tos=int(tos,0);rate=float(rate)
        if name in rows or not 1<=port<=65535 or not 0<=tos<=255 or not math.isfinite(rate) or rate<=0: raise ValueError('invalid flow')
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.setsockopt(socket.IPPROTO_IP,socket.IP_TOS,tos)
        sock.connect((a.destination,port));gap=a.size*8/(rate*1e6)
        rows[name]={'sent':0,'payload_bytes':0,'tos':tos,'requested_payload_mbps':rate,'port':port}
        heapq.heappush(q,(start,i,name,sock,gap))
    while q:
        due,i,name,sock,gap=heapq.heappop(q)
        now=time.monotonic()
        if due>=end or now>=end: break
        if due>now: time.sleep(due-now)
        row=rows[name]
        for _ in range(a.burst):
            stamp=time.monotonic_ns()
            data=HEADER.pack(MAGIC,row['sent'],stamp)+bytes(a.size-HEADER.size)
            sock.send(data);row['sent']+=1;row['payload_bytes']+=len(data)
        heapq.heappush(q,(due+gap*a.burst,i,name,sock,gap))
    # Include the complete requested observation window, even after its last packet.
    time.sleep(max(0,end-time.monotonic()))
    elapsed=time.monotonic()-start
    for row in rows.values(): row['actual_payload_mbps']=row['payload_bytes']*8/elapsed/1e6
    print(json.dumps({'elapsed_seconds':elapsed,'udp_payload_size':a.size,'packets_per_burst':a.burst,'flows':rows}),flush=True)

def receive(a):
    sel=selectors.DefaultSelector();rows={};start=time.monotonic();end=start+a.seconds
    for port in a.port:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,4*1024*1024)
        s.setsockopt(socket.IPPROTO_IP,socket.IP_RECVTOS,1);s.bind(('0.0.0.0',port));s.setblocking(False)
        sel.register(s,selectors.EVENT_READ,port)
        rows[port]={'received':0,'payload_bytes':0,'duplicates':0,'tos_counts':{},'sequences':set(),'delays_ms':[],'arrival_ns':[],'socket_rcvbuf_bytes':s.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF)}
    print('READY',flush=True)
    while time.monotonic()<end:
        for key,_ in sel.select(min(.1,max(0,end-time.monotonic()))):
            data,anc,flags,addr=key.fileobj.recvmsg(65535,256);now=time.monotonic_ns()
            if len(data)<HEADER.size: continue
            magic,seq,sent=HEADER.unpack_from(data)
            if magic!=MAGIC: continue
            r=rows[key.data];r['received']+=1;r['payload_bytes']+=len(data)
            if seq in r['sequences']: r['duplicates']+=1
            r['sequences'].add(seq);r['delays_ms'].append((now-sent)/1e6);r['arrival_ns'].append(now)
            for level,kind,value in anc:
                if level==socket.IPPROTO_IP and kind==socket.IP_TOS:
                    tos=str(value[0]);r['tos_counts'][tos]=r['tos_counts'].get(tos,0)+1
    for r in rows.values():
        delays=sorted(r.pop('delays_ms'));arr=r.pop('arrival_ns');r['unique_received']=len(r.pop('sequences'))
        r['delay_ms']={str(p):delays[min(len(delays)-1,math.ceil(p/100*len(delays))-1)] if delays else None for p in [50,95,99,100]}
        r['first_to_last_seconds']=(arr[-1]-arr[0])/1e9 if len(arr)>1 else None
        r['receive_payload_mbps']=r['payload_bytes']*8/r['first_to_last_seconds']/1e6 if len(arr)>1 else None
    print(json.dumps({'observation_seconds':time.monotonic()-start,'ports':rows}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    tx=sub.add_parser('send');tx.add_argument('--destination',default='10.0.2.10');tx.add_argument('--seconds',type=positive,default=8)
    tx.add_argument('--size',type=int,default=1000);tx.add_argument('--flow',action='append',required=True,help='name:port:TOS:payload-Mbit/s')
    tx.add_argument('--burst',type=int,default=1,help='packets released together per pacing interval')
    rx=sub.add_parser('receive');rx.add_argument('--seconds',type=positive,default=11);rx.add_argument('--port',type=int,action='append',required=True)
    a=p.parse_args()
    if a.mode=='send':
        if not HEADER.size<=a.size<=1400: p.error('size must be 20..1400 bytes')
        if not 1<=a.burst<=1000: p.error('burst must be 1..1000 packets')
        send(a)
    else:
        if len(set(a.port))!=len(a.port) or any(not 1<=x<=65535 for x in a.port): p.error('ports must be unique and in 1..65535')
        receive(a)
