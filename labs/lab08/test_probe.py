import subprocess,unittest
from unittest.mock import patch
import probe

class ProbeTests(unittest.TestCase):
    def dns(self,text):
        with patch('probe.subprocess.run',return_value=subprocess.CompletedProcess([],0,text,'')) as run:
            result=probe.check_dns();self.assertEqual(run.call_args.kwargs['timeout'],4);return result
    def response(self):
        data=bytearray(48);data[0]=0x24;data[1]=10;data[24:32]=b'12345678';return data
    def check(self,data=None,peer=(probe.SERVER,123),token=b'12345678'):
        return probe.check_ntp(self.response() if data is None else data,peer,token)
    def test_fixed_dns_answer(self):self.assertEqual(self.dns(probe.SERVER+'\n')['observed_answers'],[probe.SERVER])
    def test_wrong_empty_multiple_or_alias_dns_rejected(self):
        for answer in ['', '10.10.14.11\n',probe.SERVER+'\n10.10.14.11\n','alias.example.\n'+probe.SERVER+'\n']:
            with self.subTest(answer=answer),self.assertRaises(RuntimeError):self.dns(answer)
    def test_dns_tool_error_not_service_success(self):
        for error in [FileNotFoundError(),subprocess.TimeoutExpired('dig',4),subprocess.CalledProcessError(9,'dig')]:
            with patch('probe.subprocess.run',side_effect=error),self.assertRaises(type(error)):probe.check_dns()
    def test_valid_ntp_versions(self):
        for version in [3,4]:
            data=self.response();data[0]=(version<<3)|4;self.assertEqual(self.check(data)['stratum'],10)
    def test_ntp_peer(self):
        for peer in [('192.0.2.1',123),(probe.SERVER,124)]:
            with self.assertRaises(RuntimeError):self.check(peer=peer)
    def test_ntp_short(self):
        with self.assertRaises(RuntimeError):self.check(bytearray(47))
    def test_ntp_origin_token(self):
        with self.assertRaises(RuntimeError):self.check(token=b'87654321')
    def test_ntp_mode(self):
        data=self.response();data[0]=0x23
        with self.assertRaises(RuntimeError):self.check(data)
    def test_ntp_version(self):
        data=self.response();data[0]=4
        with self.assertRaises(RuntimeError):self.check(data)
    def test_ntp_alarm(self):
        data=self.response();data[0]|=0xc0
        with self.assertRaises(RuntimeError):self.check(data)
    def test_ntp_unexpected_stratum(self):
        for stratum in [0,1,16,255]:
            data=self.response();data[1]=stratum
            with self.assertRaises(RuntimeError):self.check(data)

if __name__=='__main__':unittest.main()
