#!/usr/bin/env python3
"""Send one actual Lab32 CoA or Disconnect from the radius node."""
import argparse,json,re,subprocess as sp,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--directory',type=Path,default=Path('/run/netbook32/config'))
p.add_argument('--dictionary',type=Path)
p.add_argument('--secret-file',type=Path)
p.add_argument('--event-time',type=int)
p.add_argument('kind',choices=['coa','disconnect'])
p.add_argument('line');p.add_argument('session_id');p.add_argument('--profile')
a=p.parse_args()
for value in [a.line,a.session_id,a.profile]:
    if value is not None and not re.fullmatch(r'[A-Za-z0-9:-]{1,128}',value):p.error('Invalid lab attribute value')
if a.kind=='coa' and a.profile is None:p.error('CoA needs --profile')
if a.kind=='disconnect' and a.profile is not None:p.error('Disconnect does not take --profile')
attrs=[f'User-Name = "{a.line}"',f'Acct-Session-Id = "{a.session_id}"',
       f'Event-Timestamp = {int(time.time()) if a.event_time is None else a.event_time}',
       'Message-Authenticator = 0x00']
if a.profile is not None:attrs.append(f'Filter-Id = "{a.profile}"')
cmd=['radclient','-x','-r','1','-t','3','-S',str(a.secret_file or a.directory/'coa.secret')]
if a.dictionary:cmd+=['-D',str(a.dictionary)]
cmd+=['10.255.32.1:3799',a.kind]
r=sp.run(cmd,input='\n'.join(attrs)+'\n',text=True,capture_output=True,timeout=15)
print(r.stdout,end='');print(r.stderr,end='',file=__import__('sys').stderr)
raise SystemExit(r.returncode)
