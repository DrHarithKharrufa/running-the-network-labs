"""Bounded lab probes; responses do not establish production service health."""
import json,secrets,socket,subprocess,sys,time

SERVER='10.10.14.10'
NAME='srv-dc.ald.example'

def check_dns():
    result=subprocess.run(['dig','@'+SERVER,NAME,'A','+short','+time=2','+tries=1'],capture_output=True,text=True,timeout=4,check=True)
    answers=[line.strip() for line in result.stdout.splitlines() if line.strip()]
    if answers != [SERVER]:
        raise RuntimeError('DNS response is not the one configured lab A record: '+repr(answers))
    return {'name':NAME,'expected_a':SERVER,'observed_answers':answers,'claim':'explicit-server fixed A lookup only'}

def check_ntp(data,peer,token):
    if peer!=(SERVER,123) or len(data)<48 or data[0]&7!=4 or (data[0]>>3)&7 not in (3,4) or data[24:32]!=token:
        raise RuntimeError('Invalid NTP response')
    if data[0]>>6==3 or data[1]!=10:
        raise RuntimeError('NTP response does not match the configured stratum-10 lab source')
    return {'mode':data[0]&7,'stratum':data[1],'leap':data[0]>>6,'reference_id_hex':data[12:16].hex(),'claim':'response only; no UTC accuracy, authentication or clock discipline tested'}

def main():
    if len(sys.argv)<2:raise SystemExit('usage: probe.py dns|ntp|log [message]')
    mode=sys.argv[1]
    if mode=='dns':print(json.dumps(check_dns()));return
    if mode not in ('ntp','log'):raise SystemExit('usage: probe.py dns|ntp|log [message]')
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.settimeout(2)
        if mode=='ntp':
            request=bytearray(48);request[0]=0x23
            token=secrets.token_bytes(8);request[40:48]=token
            s.sendto(request,(SERVER,123));data,peer=s.recvfrom(1024)
            print(json.dumps(check_ntp(data,peer,token)))
        else:
            if len(sys.argv)!=3:raise SystemExit('usage: probe.py log MESSAGE')
            message=sys.argv[2]
            s.sendto(('<134>1 '+time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' lab08-client probe - LAB08 - '+message).encode(),(SERVER,514))
            print('UDP datagram submitted; inspect collector for receipt: '+message)

if __name__=='__main__':main()
