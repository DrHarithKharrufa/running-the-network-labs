#!/usr/bin/env python3
"""Small, isolated RADIUS authorisation/enforcement fixture, not a production BNG.

Static attachment/address bindings replace DHCP discovery in this exercise.
CoA/Disconnect packets are verified by a separate FreeRADIUS listener before
its exec module invokes the dynamic action. Never expose this fixture publicly.
"""
import argparse,json,os,subprocess as sp,sys,time,uuid,re,fcntl
from pathlib import Path

LINES={'circuit-id-0001':{'interface':'eth1','address':'100.64.1.2','prefix':'2001:db8:3200:100::/56'},
       'circuit-id-0002':{'interface':'eth2','address':'100.64.2.2','prefix':'2001:db8:3200:200::/56'}}
PROFILES={'lab-5m':'5mbit','lab-1m':'1mbit','garden':'1mbit'}

def command(a,cmd,input=None,ok=True):
    env=os.environ.copy();env.update(a.config.get('environment',{}))
    executable=a.config.get('executables',{}).get(cmd[0],cmd[0]);actual=[executable,*cmd[1:]]
    r=sp.run(actual,input=input,text=True,capture_output=True,env=env,timeout=15)
    row={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    # The shared secrets are read through radclient -S, never placed in argv.
    with (a.directory/'commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    if ok and r.returncode:raise RuntimeError(str(row))
    return r

def save(a,state):
    tmp=a.directory/'sessions.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.chmod(0o600);tmp.replace(a.directory/'sessions.json')

def firewall(a,state):
    # Complete table belongs only to this disposable router namespace.
    rules=['*filter',':INPUT ACCEPT [0:0]',':FORWARD DROP [0:0]',':OUTPUT ACCEPT [0:0]',':NBK32 - [0:0]','-A FORWARD -j NBK32']
    for line,s in state.items():
        if s.get('profile') not in PROFILES:continue
        b=LINES[line];i=b['interface'];ip=b['address']
        if s['profile']=='garden':
            rules += [f'-A NBK32 -i {i} -o eth4 -s {ip}/32 -d 203.0.113.80/32 -p tcp --dport 8080 -j ACCEPT',
                      f'-A NBK32 -i eth4 -o {i} -s 203.0.113.80/32 -d {ip}/32 -p tcp --sport 8080 -m conntrack --ctstate ESTABLISHED -j ACCEPT']
        else:
            rules += [f'-A NBK32 -i {i} -o eth4 -s {ip}/32 -d 203.0.113.0/24 -j ACCEPT',
                      f'-A NBK32 -i eth4 -o {i} -s 203.0.113.0/24 -d {ip}/32 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT']
    rules+=['-A NBK32 -j DROP','COMMIT',''];command(a,['iptables-restore'],input='\n'.join(rules))

def shape(a,line,profile):
    i=LINES[line]['interface'];rate=PROFILES[profile]
    command(a,['tc','qdisc','del','dev',i,'root'],ok=False)
    command(a,['tc','qdisc','add','dev',i,'root','handle','1:','htb','default','10'])
    command(a,['tc','class','replace','dev',i,'parent','1:','classid','1:10','htb','rate',rate,'ceil',rate,'burst','16000','cburst','16000'])
    command(a,['tc','qdisc','replace','dev',i,'parent','1:10','handle','10:','fq_codel','limit','200','noecn'])
    command(a,['tc','qdisc','del','dev',i,'ingress'],ok=False)
    command(a,['tc','qdisc','add','dev',i,'handle','ffff:','ingress'])
    command(a,['tc','filter','add','dev',i,'parent','ffff:','protocol','ip','pref','1','u32','match','ip','src',LINES[line]['address']+'/32',
               'action','police','rate',rate,'burst','16000','mtu','1500','conform-exceed','drop/ok'])

def apply(a,state,line,profile,session):
    # Deny this attachment while changing its queue objects. Others keep policy.
    temporary={k:v for k,v in state.items() if k!=line};firewall(a,temporary);save(a,temporary)
    shape(a,line,profile)
    session['profile']=profile;temporary[line]=session
    firewall(a,temporary);save(a,temporary)
    return temporary

def radius(a,kind,attributes):
    port='1812' if kind=='auth' else '1813'
    request='\n'.join(attributes)+'\n'
    return command(a,['radclient','-x','-r','1','-t','2','-S',str(a.directory/'auth.secret'),
                      a.config['radius']+':'+port,kind],input=request,ok=False)

def account(a,line,s,event):
    attrs=[f'User-Name = "{line}"',f'Acct-Session-Id = "{s["session_id"]}"',f'Acct-Status-Type = {event}',
           'NAS-IP-Address = 10.255.32.1',f'NAS-Port-Id = "{line}"',f'Class = "{s["class"]}"',
           f'Acct-Session-Time = {max(0,int(time.time()-s["started"]))}']
    r=radius(a,'acct',attrs);ack='Received Accounting-Response' in r.stdout and r.returncode==0
    with (a.directory/'accounting-journal.jsonl').open('a') as f:
        f.write(json.dumps({'line':line,'session_id':s['session_id'],'event':event,'acknowledged':ack,'attributes':attrs})+'\n')
    return ack

def attribute(text,name):
    values=re.findall(r'^\s*'+re.escape(name)+r'\s*=\s*(.+?)\s*$',text,re.M)
    if len(values)!=1:raise ValueError('missing or repeated '+name)
    return values[0].strip('"')

def env_value(name):
    v=os.environ.get(name,'')
    return v[1:-1] if len(v)>=2 and v[0]==v[-1]=='"' else v

def reject(code):
    print('Error-Cause = '+str(code),flush=True)
    return 1

def main(a):
    a.config=json.loads((a.directory/'controller.json').read_text())
    with (a.directory/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads((a.directory/'sessions.json').read_text()) if (a.directory/'sessions.json').exists() else {}
        if a.action=='init':
            firewall(a,{});save(a,{})
            return 0
        if a.action=='show':print(json.dumps(state,indent=2));return 0
        if a.action=='dynamic':
            line=env_value('USER_NAME');sid=env_value('ACCT_SESSION_ID');profile=env_value('FILTER_ID')
            if not line or not sid or not a.event_time:return reject(402)
            if abs(time.time()-a.event_time)>120:return reject(407)
            if line not in state or sid!=state[line]['session_id']:return reject(503)
            s=state[line]
            if a.dynamic_kind=='disconnect':
                new={k:v for k,v in state.items() if k!=line};firewall(a,new);save(a,new)
                account(a,line,s,'Stop');return 0
            if profile not in PROFILES:return reject(407)
            apply(a,state,line,profile,s);return 0
        line=a.line
        if line not in LINES:raise ValueError('unknown trusted attachment')
        if a.action=='down':
            s=state.pop(line,None);firewall(a,state);save(a,state)
            if s:account(a,line,s,'Stop')
            return 0
        if a.action=='interim':
            if line not in state:raise ValueError('session absent')
            return 0 if account(a,line,state[line],'Interim-Update') else 1
        # Reauthorisation first closes any old permit; failed/unknown replies stay closed.
        old=state.pop(line,None);firewall(a,state);save(a,state)
        if old:account(a,line,old,'Stop')
        identity=a.identity or line
        if not re.fullmatch(r'[a-z0-9-]{1,64}',identity):raise ValueError('invalid lab identity')
        password=a.password
        if not re.fullmatch(r'[a-z0-9-]{1,64}',password):raise ValueError('invalid lab password')
        response=radius(a,'auth',[f'User-Name = "{identity}"',f'User-Password = "{password}"',
            'NAS-IP-Address = 10.255.32.1',f'NAS-Port-Id = "{line}"','Message-Authenticator = 0x00'])
        if response.returncode or 'Received Access-Accept' not in response.stdout:
            print('AUTHORISATION DENIED',flush=True);return 1
        reply=response.stdout.split('Received Access-Accept',1)[1]
        profile=attribute(reply,'Filter-Id');ip=attribute(reply,'Framed-IP-Address')
        prefix=attribute(reply,'Delegated-IPv6-Prefix');tag=attribute(reply,'Class')
        if re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',tag):tag=bytes.fromhex(tag[2:]).decode('ascii')
        if profile not in PROFILES or ip!=LINES[line]['address'] or prefix!=LINES[line]['prefix'] or not re.fullmatch(r'[A-Za-z0-9:-]{1,64}',tag):
            print('AUTHORISATION REPLY NOT SUPPORTED',flush=True);return 1
        s={'session_id':uuid.uuid4().hex,'profile':profile,'address':ip,'delegated_prefix_metadata':prefix,'class':tag,'started':time.time()}
        apply(a,state,line,profile,s);ack=account(a,line,s,'Start')
        print(json.dumps({'line':line,**s,'accounting_start_acknowledged':ack}),flush=True)
        return 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True)
    p.add_argument('action',choices=['init','show','up','down','interim','dynamic']);p.add_argument('line',nargs='?')
    p.add_argument('--identity');p.add_argument('--password',default='line');p.add_argument('--dynamic-kind',choices=['coa','disconnect'],default='coa')
    p.add_argument('--event-time',type=int,default=0);a=p.parse_args()
    try:sys.exit(main(a))
    except BaseException as exc:
        if isinstance(exc,SystemExit):raise
        print('CONTROLLER ERROR '+repr(exc),file=sys.stderr,flush=True);sys.exit(2)
