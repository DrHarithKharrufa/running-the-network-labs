from pathlib import Path
import unittest
from policy import check
from pipeline import run

GOOD=(Path(__file__).parent/'fixtures/good.cfg').read_text('utf-8')

class Tests(unittest.TestCase):
    def test_scoped_good_state(self):self.assertEqual(check(GOOD)['status'],'PASS')
    def test_all_and_mixed_telnet_forms(self):
        for command in ['all','telnet','ssh telnet','telnet ssh']:
            with self.subTest(command=command):self.assertEqual(check(GOOD.replace('transport input ssh',f'transport input {command}'))['status'],'FAIL')
    def test_comment_or_description_is_not_command(self):
        text=GOOD.replace('description server-07','description transport input telnet')
        self.assertEqual(check('! transport input all\n'+text)['status'],'PASS')
    def test_last_explicit_transport_state(self):
        self.assertEqual(check(GOOD.replace(' transport input ssh',' transport input telnet\n transport input ssh'))['status'],'PASS')
    def test_uncovered_vty_is_unknown(self):
        self.assertEqual(check(GOOD.replace('line vty 5 15','line vty 5 10'))['status'],'UNSUPPORTED')
    def test_missing_transport_default_is_unknown(self):
        self.assertEqual(check(GOOD.replace(' transport input ssh',''))['status'],'UNSUPPORTED')
    def test_no_default_and_unknown_transport(self):
        for cmd in ['no transport input','default transport input','transport input ssh rlogin','transport input none ssh']:
            with self.subTest(cmd=cmd):self.assertEqual(check(GOOD.replace('transport input ssh',cmd))['status'],'UNSUPPORTED')
    def test_none_disables_input_within_profile(self):
        self.assertEqual(check(GOOD.replace('transport input ssh','transport input none'))['status'],'PASS')
    def test_interface_description_scope(self):
        self.assertEqual(check(GOOD.replace(' description server-07\n',''))['status'],'FAIL')
        self.assertEqual(check(GOOD.replace('end','interface GigabitEthernet1/0/9\n no shutdown\nend'))['status'],'PASS')
    def test_absent_owned_interface(self):
        self.assertEqual(check(GOOD,('GigabitEthernet1/0/99','Loopback0'))['status'],'UNSUPPORTED')
    def test_loopback_allocation_and_prefix(self):
        for addr,mask in [('10.254.0.1','255.255.255.255'),('10.255.0.1','255.255.255.0')]:
            self.assertEqual(check(GOOD.replace('10.255.0.1 255.255.255.255',f'{addr} {mask}'))['status'],'FAIL')
    def test_invalid_address(self):
        self.assertEqual(check(GOOD.replace('10.255.0.1','999.0.0.1'))['status'],'FAIL')
    def test_banner_and_ranges_unsupported(self):
        for prefix in ['banner motd ^\n','interface range GigabitEthernet1/0/1 - 8\n']:
            self.assertEqual(check(prefix+GOOD)['status'],'UNSUPPORTED')
    def test_acl_does_not_invent_reachability(self):
        candidate=GOOD.replace('end','ip access-list extended EDGE\n permit ip any any\n deny ip any any\nend')
        r=run(GOOD,candidate);self.assertEqual(r['stages']['candidate_policy']['status'],'PASS');self.assertEqual(r['stages']['batfish']['status'],'NOT_RUN')
    def test_current_and_candidate_both_checked(self):
        r=run(GOOD.replace('transport input ssh','transport input all'),GOOD)
        self.assertEqual(r['stages']['current_policy']['status'],'FAIL');self.assertEqual(r['stages']['candidate_policy']['status'],'PASS')
    def test_missing_integrations_block_promotion(self):
        r=run(GOOD,GOOD);self.assertTrue(r['promotion'].startswith('BLOCKED'))
        for key in ['batfish','NOS_integration','service_canary','deployment']:self.assertEqual(r['stages'][key]['status'],'NOT_RUN')
    def test_hash_binds_exact_input(self):
        r=run(GOOD,GOOD+'\n');self.assertNotEqual(r['artefact_hashes']['current'],r['artefact_hashes']['candidate'])
    def test_nonconfiguration_rejected(self):
        for obj in [None,'',[],{}]:self.assertEqual(check(obj)['status'],'UNSUPPORTED')
    def test_interface_deletion_and_default_not_ignored(self):
        for command in ['no interface Loopback0','default interface Loopback0']:
            self.assertEqual(check(GOOD.replace('end',command+'\nend'))['status'],'UNSUPPORTED')
    def test_unindented_transport_not_ignored(self):
        self.assertEqual(check(GOOD.replace('end','transport input all\nend'))['status'],'UNSUPPORTED')

if __name__=='__main__':unittest.main(verbosity=2)
