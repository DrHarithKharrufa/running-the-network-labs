"""Execute Bash acceptance logic with a local docker command double, never Docker."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

DOCKER = '''#!/usr/bin/env python3
import os,sys,json
from pathlib import Path
p=Path(os.environ['DOUBLE_STATE']);mode=os.environ['DOUBLE_MODE']
state=json.loads(p.read_text()) if p.exists() else {'probes':0,'down':0,'restores':0}
args=sys.argv[1:];result=0
if 'ping' in args:
    i=state['probes'];state['probes']+=1
    received=0 if i==1 else 5
    result=1 if i==1 else 0
    if mode=='partial' and i==0: received=4
    if mode=='negative_command_error' and i==1: result=127
    if mode=='unexpected_negative_success' and i==1: received=5;result=0
    if mode=='wrong_negative_count' and i==1: received=1
    if mode=='lost_restoration' and i==2: received=0;result=1
    if mode=='missing_summary' and i==0: print('unrecognised output')
    else: print(f'5 packets transmitted, {received} '+('packets ' if mode=='busybox' else '')+f'received, {(5-received)*20}% packet loss')
elif 'down' in args: state['down']+=1
elif 'up' in args:
    state['restores']+=1
    if mode=='restore_error': result=1
p.write_text(json.dumps(state))
sys.exit(result)
'''

@unittest.skipUnless(shutil.which('bash'), 'requires Bash; no network engine required')
class VerifyTests(unittest.TestCase):
    def run_case(self, mode):
        import json
        with tempfile.TemporaryDirectory(prefix='rtn-lab03-double-') as td:
            root=Path(td);stub=root/'docker';stub.write_text(DOCKER);stub.chmod(0o700)
            state=root/'state.json'
            env=os.environ|{'PATH':str(root)+os.pathsep+os.environ['PATH'],'DOUBLE_STATE':str(state),'DOUBLE_MODE':mode}
            r=subprocess.run(['bash',str(Path(__file__).with_name('verify.sh'))],env=env,capture_output=True,text=True)
            return r,json.loads(state.read_text())
    def test_complete_positive_fault_restore(self):
        for mode in ['normal','busybox']:
            r,s=self.run_case(mode);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertEqual((s['probes'],s['down'],s['restores']),(3,1,1))
    def test_partial_positive_not_accepted(self):
        r,s=self.run_case('partial');self.assertNotEqual(r.returncode,0);self.assertEqual(s['down'],0)
    def test_missing_summary_not_accepted(self):
        r,s=self.run_case('missing_summary');self.assertNotEqual(r.returncode,0);self.assertEqual(s['down'],0)
    def test_command_error_is_not_expected_loss(self):
        r,s=self.run_case('negative_command_error');self.assertNotEqual(r.returncode,0);self.assertEqual(s['restores'],1)
    def test_negative_must_fail(self):
        r,s=self.run_case('unexpected_negative_success');self.assertNotEqual(r.returncode,0);self.assertEqual(s['restores'],1)
    def test_negative_must_receive_zero(self):
        r,s=self.run_case('wrong_negative_count');self.assertNotEqual(r.returncode,0);self.assertEqual(s['restores'],1)
    def test_restored_path_must_reply(self):
        r,s=self.run_case('lost_restoration');self.assertNotEqual(r.returncode,0);self.assertEqual(s['probes'],3)
    def test_restore_error_cannot_print_pass(self):
        r,s=self.run_case('restore_error');self.assertNotEqual(r.returncode,0)
        self.assertNotIn('PASS:',r.stdout);self.assertEqual(s['restores'],2)

if __name__=='__main__':unittest.main()
