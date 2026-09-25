"""Bash fault-helper acceptance with Docker command doubles; no packets."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,unittest
DOUBLE='''#!/usr/bin/env python3
from pathlib import Path
import json,os,sys
p=Path(os.environ['DOUBLE_STATE']);s=json.loads(p.read_text());mode=os.environ['DOUBLE_MODE'];a=sys.argv[1:]
assert a[:3]==['exec','clab-lab09-fw','iptables'];a=a[3:];s['calls'].append(a);rc=0
if a[0]=='-S':
    if mode=='read_error':rc=1
    else:
        print('-P FORWARD DROP')
        for i in range(s['rules']):print('-A FORWARD -m comment --comment LAB09-RETURN-FAULT -j DROP')
elif a[0]=='-D':
    if mode=='delete_error':rc=1
    else:s['rules']-=1
elif a[0]=='-C':rc=int(mode=='conflict' or not s['rules'])
elif a[0]=='-I':s['rules']+=1
elif a[0]!='-nvxL':raise AssertionError(a)
p.write_text(json.dumps(s));sys.exit(rc)
'''
@unittest.skipUnless(shutil.which('bash'),'Bash required')
class FaultTests(unittest.TestCase):
    def run_case(self,action,mode='normal',rules=0):
        with tempfile.TemporaryDirectory(prefix='rtn-lab09-double-') as td:
            root=Path(td);stub=root/'docker';stub.write_text(DOUBLE);stub.chmod(0o700)
            state=root/'state.json';state.write_text(json.dumps({'rules':rules,'calls':[]}))
            env=os.environ|{'PATH':str(root)+os.pathsep+os.environ['PATH'],'DOUBLE_STATE':str(state),'DOUBLE_MODE':mode}
            r=subprocess.run(['bash',str(Path(__file__).with_name('fault.sh')),action],env=env,capture_output=True,text=True,timeout=10)
            return r,json.loads(state.read_text())
    def test_block_and_existing_rule(self):
        for rules in [0,1]:
            r,s=self.run_case('block',rules=rules);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(s['rules'],1)
    def test_restore_absent_single_and_duplicates(self):
        for rules in [0,1,2]:
            r,s=self.run_case('restore',rules=rules);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(s['rules'],0)
            self.assertFalse(any('-F' in a for a in s['calls']))
    def test_inspection_error_both_actions(self):
        for action in ['block','restore']:
            r,s=self.run_case(action,'read_error',1);self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],1)
    def test_conflicting_comment_fails(self):
        r,s=self.run_case('block','conflict',1);self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],1)
    def test_delete_error_fails(self):
        r,s=self.run_case('restore','delete_error',1);self.assertNotEqual(r.returncode,0);self.assertEqual(s['rules'],1)
    def test_invalid_action_no_device_call(self):
        r,s=self.run_case('typo');self.assertEqual(r.returncode,2);self.assertEqual(s['calls'],[])
if __name__=='__main__':unittest.main()
