#!/usr/bin/env python3
"""Create a private disposable Lab32 RADIUS/controller configuration."""
from pathlib import Path
import json,secrets,argparse,shutil,os

def create(dest,prefix=Path('/'),lab=None):
    dest=dest.resolve();dest.mkdir(parents=False,exist_ok=False,mode=0o700)
    lab=(lab or Path(__file__).parent).resolve()
    auth=secrets.token_hex(24);coa=secrets.token_hex(24)
    def write(name,s):
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n');p.chmod(0o600)
    write('auth.secret',auth+'\n');write('coa.secret',coa+'\n')
    executables={n:shutil.which(n) or n for n in ['iptables-restore','tc','radclient']}
    environment={n:os.environ[n] for n in ['PATH','LD_LIBRARY_PATH','XTABLES_LIBDIR'] if n in os.environ}
    write('controller.json',json.dumps({'radius':'10.255.32.2','executables':executables,'environment':environment},indent=2)+'\n')
    users=''
    for name,ip,prefix6,profile in [('circuit-id-0001','100.64.1.2','2001:db8:3200:100::/56','lab-5m'),('circuit-id-0002','100.64.2.2','2001:db8:3200:200::/56','lab-1m'),('bad-profile','100.64.1.2','2001:db8:3200:100::/56','unsupported')]:
        users+=f'''{name} Cleartext-Password := "line"
    Framed-IP-Address = {ip},
    Delegated-IPv6-Prefix = {prefix6},
    Filter-Id = "{profile}",
    Class = "lab32:{name}"

'''
    write('aaa/users',users)
    common=f'''prefix = "{prefix}/usr"
libdir = "{prefix}/usr/lib/freeradius"
max_requests = 64
log {{
 destination = stdout
 auth = no
}}
security {{
 allow_core_dumps = no
}}
'''
    write('aaa/dictionary','');write('dynamic/dictionary','')
    aaa=common+f'''logdir = "{dest}/aaa"
run_dir = "{dest}/aaa"
pidfile = "{dest}/aaa/radius.pid"
client bng {{
 ipaddr = 10.255.32.1
 secret = {auth}
 require_message_authenticator = yes
}}
modules {{
 files {{
  filename = "{dest}/aaa/users"
 }}
 pap {{
  normalise = yes
 }}
 detail {{
  filename = "{dest}/aaa/accounting-detail"
  permissions = 0600
 }}
}}
server aaa {{
 listen {{
  type = auth
  ipaddr = 10.255.32.2
  port = 1812
 }}
 listen {{
  type = acct
  ipaddr = 10.255.32.2
  port = 1813
 }}
 authorize {{
  files
  pap
 }}
 authenticate {{
  Auth-Type PAP {{
   pap
  }}
 }}
 accounting {{
  detail
 }}
}}
'''
    write('aaa/radiusd.conf',aaa)
    dynamic=common+f'''logdir = "{dest}/dynamic"
run_dir = "{dest}/dynamic"
pidfile = "{dest}/dynamic/radius.pid"
client authorised_dac {{
 ipaddr = 10.255.32.2
 secret = {coa}
 require_message_authenticator = yes
}}
modules {{
 always reject {{
  rcode = reject
 }}
'''
    for name in ['coa','disconnect']:
        dynamic+=f''' exec apply_{name} {{
  wait = yes
  program = "/usr/bin/python3 {lab}/subscriber.py --directory {dest} dynamic --dynamic-kind {name} --event-time %{{integer:Event-Timestamp}}"
  input_pairs = request
  output_pairs = reply
  shell_escape = yes
  timeout = 10
 }}
'''
    dynamic+='}\nserver dynamic {\n listen {\n  type = coa\n  ipaddr = 10.255.32.1\n  port = 3799\n }\n recv-coa {\n'
    dynamic+='''  if (!&User-Name || !&Acct-Session-Id || !&Event-Timestamp) {
   update reply {
    Error-Cause := 402
   }
   reject
  }
  if ("%{Packet-Type}" == "Disconnect-Request") {
   apply_disconnect
  } else {
   apply_coa
  }
 }
}
'''
    write('dynamic/radiusd.conf',dynamic)
    return dest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--prefix',type=Path,default=Path('/'))
    a=p.parse_args();print(create(a.destination,a.prefix))
