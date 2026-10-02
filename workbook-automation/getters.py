"""Read-only NAPALM example. Requires a protected, qualified backend manifest."""
import argparse,json,os
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('inventory');p.add_argument('--out',required=True);a=p.parse_args()
 i=json.loads(Path(a.inventory).read_text(encoding='utf8'))
 if i.get('lab_owned') is not True or i.get('transport_trust_verified') is not True:raise ValueError('ownership/trust gate incomplete')
 if i['driver'] not in ['ios','nxos_ssh','eos','junos','iosxr_netconf','srlinux']:raise ValueError('driver not allowlisted')
 options=i['backend_options']
 if options.get('insecure') or options.get('skip_verify'):raise ValueError('unverified transport refused')
 if i['driver']=='srlinux' and not options.get('tls_ca'):raise ValueError('SR Linux trusted CA required')
 from napalm import get_network_driver
 with get_network_driver(i['driver'])(i['host'],os.environ[i['username_env']],os.environ[i['password_env']],optional_args=options) as d:
  data={'facts':d.get_facts(),'interfaces':d.get_interfaces()}
  if i['owned_interface'] not in data['interfaces']:raise ValueError('declared interface absent: do not fabricate defaults')
 Path(a.out).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
 print('Saved getter result. Protect identifiers; independently verify the native owned interface.')
if __name__=='__main__':main()
