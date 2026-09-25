"""Exercise Bash error handling with a Docker command double; no network changes."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,unittest

DOUBLE='''#!/usr/bin/env python3
from pathlib import Path
import json,os,sys
p=Path(os.environ['DOUBLE_STATE']);s=json.loads(p.read_text());mode=os.environ['DOUBLE_MODE'];a=sys.argv[1:]
assert a[:2]==['exec','clab-lab07-rtr'];a=a[2:];s['calls'].append(a);rc=0
if a[:3]==['tc','qdisc','show']:
    if mode=='qdisc_read_error':rc=127
    else:print('qdisc netem 8001: root delay 80ms' if s['qdisc'][a[-1]] else 'qdisc noqueue 0: root')
elif a[:3]==['tc','qdisc','del']:
    if mode=='qdisc_delete_error':rc=1
    else:s['qdisc'][a[4]]=False
elif a[:3]==['tc','qdisc','replace']:s['qdisc'][a[4]]=True
elif a[:3]==['ip','link','set']:
    if mode=='mtu_error':rc=1
    else:s['mtu']=int(a[-1])
elif a[:2]==['iptables','-S']:
    if mode=='firewall_read_error':rc=1
    else:
        print('-P OUTPUT ACCEPT')
        for i in range(s['rules']):print('-A OUTPUT -p icmp -m icmp --icmp-type 3/4 -m comment --comment LAB07-MTU -j DROP')
elif a[:2]==['iptables','-D']:
    if mode=='firewall_delete_error':rc=1
    else:s['rules']-=1
elif a[:2]==['iptables','-A']:s['rules']+=1
elif a[:3]==['tc','-s','qdisc'] or a[:3]==['ip','-details','link']:pass
else:raise AssertionError(a)
p.write_text(json.dumps(s));sys.exit(rc)
'''

@unittest.skipUnless(shutil.which('bash'),'Bash required')
class ImpairTests(unittest.TestCase):
    def run_case(self,mode='normal',action='clear'):
        with tempfile.TemporaryDirectory(prefix='rtn-lab07-double-') as td:
            root=Path(td);stub=root/'docker';stub.write_text(DOUBLE);stub.chmod(0o700)
            state=root/'state.json';state.write_text(json.dumps({'qdisc':{'eth1':True,'eth2':True},'rules':2,'mtu':1400,'calls':[]}))
            env=os.environ|{'PATH':str(root)+os.pathsep+os.environ['PATH'],'DOUBLE_STATE':str(state),'DOUBLE_MODE':mode}
            r=subprocess.run(['bash',str(Path(__file__).with_name('impair.sh')),action],env=env,capture_output=True,text=True,timeout=10)
            return r,json.loads(state.read_text())
    def test_clear_removes_exact_rules_and_impairments(self):
        r,s=self.run_case();self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((s['rules'],s['mtu']), (0,1500));self.assertFalse(any(s['qdisc'].values()))
        self.assertFalse(any('-F' in a or '--flush' in a for a in s['calls']))
    def test_qdisc_inspection_error_fails(self):
        r,s=self.run_case('qdisc_read_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],2)
    def test_qdisc_delete_error_fails(self):
        r,s=self.run_case('qdisc_delete_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],2)
    def test_firewall_inspection_error_is_not_absence(self):
        r,s=self.run_case('firewall_read_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],2)
    def test_firewall_delete_error_fails(self):
        r,s=self.run_case('firewall_delete_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],2)
    def test_mtu_error_fails(self):
        r,s=self.run_case('mtu_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['mtu'],1400)
    def test_requested_conditions_after_clean_baseline(self):
        for action in ['baseline','latency','symmetric','loss','both','mtu']:
            with self.subTest(action=action):
                r,s=self.run_case(action=action);self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(s['rules'],int(action=='mtu'))
                self.assertEqual(s['mtu'],1400 if action=='mtu' else 1500)
                self.assertEqual(s['qdisc']['eth1'],action=='symmetric')
                self.assertEqual(s['qdisc']['eth2'],action in ['latency','symmetric','loss','both'])
    def test_invalid_action_has_no_device_calls(self):
        r,s=self.run_case(action='unknown');self.assertEqual(r.returncode,2);self.assertEqual(s['calls'],[])

if __name__=='__main__':unittest.main()
