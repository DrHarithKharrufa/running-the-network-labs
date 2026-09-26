"""Boundary regression tests; no Docker or host-network operations occur."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
import unittest
from unittest.mock import patch
import netlab


class ObservationTests(unittest.TestCase):
    def check(self, text, cap=None, code=0):
        return netlab.validate_capture(cap or {'cmd': 'show state', 'expect': 'Full'},
                                       CompletedProcess([], code, text, ''))

    def test_healthy(self):
        self.assertEqual(self.check('Neighbor ID State\n10.0.0.1 Full\n'), [])

    def test_empty_negative_is_unknown(self):
        self.assertTrue(self.check('', {'expect': '(?s)^(?!.*prefix).*$', 'require': ['LSP ID']}))

    def test_cli_errors_negative_fail(self):
        for error in ('% Unknown command', '% Invalid input', 'Permission denied', 'Failed to connect'):
            with self.subTest(error=error):
                self.assertTrue(self.check(error, {'expect': '(?s)^(?!.*prefix).*$', 'require': ['LSP ID']}))

    def test_structure_before_absence(self):
        cap={'expect': '(?s)^(?!.*10.0.0.1).*$', 'require': ['LSP ID', '2 LSPs']}
        self.assertTrue(self.check('unrelated nonempty data',cap))
        self.assertTrue(self.check('LSP ID\ntruncated',cap))
        self.assertEqual(self.check('LSP ID\n2 LSPs\n',cap),[])

    def test_negative_without_contract_rejected(self):
        self.assertTrue(self.check('anything', {'expect': '(?!prefix)'}))

    def test_zero_loss_is_exact(self):
        for loss in (5, 10, 50, 100):
            with self.subTest(loss=loss):
                self.assertTrue(self.check(f'{loss}% packet loss', {'cli':'shell','expect':'0% packet loss'}))
                self.assertTrue(self.check(f'{loss}% packet loss', {'cli':'shell','packet_loss':0}))
        self.assertEqual(self.check('3 packets transmitted, 3 received, 0% packet loss',
                                   {'cli':'shell','packet_loss':0}), [])

    def test_ambiguous_ping_rejected(self):
        self.assertTrue(self.check('0% packet loss\n50% packet loss', {'cli':'shell','packet_loss':0}))

    def test_exit_status(self):
        self.assertTrue(self.check('Full', code=1))
        self.assertEqual(self.check('Network unreachable', {'cli':'shell','returncodes':[1,2],
                                                         'expect':'Network unreachable'},2), [])

    def test_allow_only_expected_absence_message(self):
        cap={'expect':'Network not in table','allow_messages':['% Network not in table']}
        self.assertEqual(self.check('% Network not in table\n',cap),[])
        self.assertTrue(self.check('% Network not in table\n% Unknown command',cap))

    def test_hash_serialized_output_exactly(self):
        topo={'name':'test','nodes':{'r1':{'image':'fixture'}},'capture':[{'node':'r1','cmd':'show state','expect':'Full'}]}
        with tempfile.TemporaryDirectory() as td, patch.object(netlab,'image_facts',return_value={}), \
             patch.object(netlab,'sh',return_value=CompletedProcess([],0,'Full\n\n','warning\n')), \
             contextlib.redirect_stdout(io.StringIO()):
            path=Path(td)/'record.json'
            self.assertEqual(netlab.capture(topo,str(path),0),0)
            entry=json.loads(path.read_text())['captures'][0]
            self.assertEqual(entry['output'],'Full\n\nwarning\n')
            self.assertEqual(entry['sha256'],hashlib.sha256(entry['output'].encode()).hexdigest())

    def test_cleanup_for_start_and_config_failure(self):
        for fail in ('up','configure'):
            calls=[]
            def step(name):
                def run(*args):
                    calls.append(name)
                    if name==fail: raise RuntimeError('original setup failure')
                return run
            with patch.object(netlab,'load',return_value={'name':'test','nodes':{}}), \
                 patch.object(netlab,'up',side_effect=step('up')), \
                 patch.object(netlab,'configure',side_effect=step('configure')), \
                 patch.object(netlab,'down',side_effect=step('down')), \
                 patch('sys.argv',['netlab','run','fixture']):
                with self.assertRaisesRegex(RuntimeError,'original setup failure'): netlab.main()
            self.assertEqual(calls[-1],'down')

    def test_keep_option(self):
        with patch.object(netlab,'load',return_value={}), patch.object(netlab,'up',side_effect=RuntimeError), \
             patch.object(netlab,'down') as down, patch('sys.argv',['netlab','run','fixture','--keep']):
            with self.assertRaises(RuntimeError): netlab.main()
            down.assert_not_called()

    def test_cleanup_does_not_delete_unowned_links(self):
        with patch.object(netlab,'sh') as shell, contextlib.redirect_stdout(io.StringIO()):
            netlab.down({'name':'test','nodes':{'r1':{}},'_owned':[],
                         'links':[{'endpoints':['r1:eth1','r2:eth1']}]})
            shell.assert_not_called()

    def test_cleanup_removes_only_created_host_endpoints(self):
        with patch.object(netlab,'sh') as shell, contextlib.redirect_stdout(io.StringIO()):
            netlab.down({'name':'test','nodes':{},'_owned':[], '_host_veth':['rtowned0a']})
            shell.assert_called_once_with(['ip','link','del','rtowned0a'],check=False)

    def test_original_error_survives_cleanup_error(self):
        with patch.object(netlab,'load',return_value={}), \
             patch.object(netlab,'up',side_effect=RuntimeError('original')), \
             patch.object(netlab,'down',side_effect=ValueError('cleanup')), \
             patch('sys.argv',['netlab','run','fixture']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError,'original'): netlab.main()


if __name__=='__main__': unittest.main(verbosity=2)
