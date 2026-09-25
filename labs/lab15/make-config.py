"""Generate disposable EAP-TLS lab PKI/configuration; never use this CA in production.

Requires Python cryptography. No host configuration or trust store is changed.
The destination must not exist. TLS 1.2 is fixed for this bounded lab; production
revocation, enrolment, authorisation databases and TLS 1.3 are separate work.
"""
import argparse,datetime,secrets
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def create(dest,prefix=Path('/')):
 dest=dest.resolve();dest.mkdir(mode=0o700,parents=False,exist_ok=False)
 now=datetime.datetime.now(datetime.timezone.utc)
 def key():return rsa.generate_private_key(public_exponent=65537,key_size=2048)
 def name(cn):return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,cn)])
 ca_key=key();ca_name=name('NetBook disposable lab CA')
 ca=(x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
  .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
  .not_valid_before(now-datetime.timedelta(minutes=5)).not_valid_after(now+datetime.timedelta(days=7))
  .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
  .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True)
  .sign(ca_key,hashes.SHA256()))
 def write(n,s):
  p=dest/n;p.write_text(s,encoding='utf-8',newline='\n');p.chmod(0o600)
 write('ca.pem',ca.public_bytes(serialization.Encoding.PEM).decode())
 for stem,cn,server,expired in [('server','radius.example.test',True,False),('alice','alice',False,False),('bob','bob',False,False),('expired','alice',False,True)]:
  k=key();end=now-datetime.timedelta(days=1) if expired else now+datetime.timedelta(days=2)
  cert=(x509.CertificateBuilder().subject_name(name(cn)).issuer_name(ca_name)
   .public_key(k.public_key()).serial_number(x509.random_serial_number())
   .not_valid_before(now-datetime.timedelta(days=2)).not_valid_after(end)
   .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
   .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if server else ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False)
   .add_extension(x509.SubjectAlternativeName([x509.DNSName(cn)]),critical=False)
   .sign(ca_key,hashes.SHA256()))
  write(stem+'.pem',cert.public_bytes(serialization.Encoding.PEM).decode())
  write(stem+'.key',k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode())
 secret=secrets.token_hex(24)
 write('hostapd.conf',f'''interface=eth1
driver=wired
ieee8021x=1
use_pae_group_addr=1
own_ip_addr=192.0.2.1
nas_identifier=netbook15-wired
radius_request_cui=0
radius_auth_req_attr=61:d:15
radius_auth_req_attr=77:s:Wired EAP-TLS lab
auth_server_addr=192.0.2.2
auth_server_port=1812
auth_server_shared_secret={secret}
eap_reauth_period=3600
''')
 for profile,identity,stem,domain in [('valid','alice','alice','radius.example.test'),('wrong-name','alice','alice','unexpected.example.test'),('expired','alice','expired','radius.example.test'),('policy-reject','bob','bob','radius.example.test')]:
  write(profile+'.conf',f'''ap_scan=0
eapol_version=2
network={{
 key_mgmt=IEEE8021X
 eap=TLS
 identity="{identity}"
 ca_cert="{dest}/ca.pem"
 domain_match="{domain}"
 client_cert="{dest}/{stem}.pem"
 private_key="{dest}/{stem}.key"
 phase1="tls_disable_tlsv1_3=1"
}}
''')
 write('dictionary','')
 write('radiusd.conf',f'''prefix = "{prefix}/usr"
libdir = "{prefix}/usr/lib/freeradius"
logdir = "{dest}"
run_dir = "{dest}"
pidfile = "{dest}/radius.pid"
max_requests = 1024
log {{
 destination = stdout
 auth = no
}}
security {{
 allow_core_dumps = no
}}
client lab_authenticator {{
 ipaddr = 192.0.2.1
 secret = {secret}
 require_message_authenticator = yes
}}
modules {{
 eap {{
  default_eap_type = tls
  ignore_unknown_eap_types = no
  tls-config tls-lab {{
   private_key_file = "{dest}/server.key"
   certificate_file = "{dest}/server.pem"
   ca_file = "{dest}/ca.pem"
   check_cert_cn = %{{User-Name}}
   tls_min_version = "1.2"
   tls_max_version = "1.2"
   cipher_list = "DEFAULT"
   ecdh_curve = "prime256v1"
  }}
  tls {{
   tls = tls-lab
   virtual_server = cert-policy
  }}
 }}
}}
server cert-policy {{
 authorize {{
  if (&TLS-Client-Cert-Common-Name == "alice") {{
   update control {{
    Auth-Type := Accept
   }}
  }} else {{
   update control {{
    Auth-Type := Reject
   }}
  }}
 }}
}}
server lab {{
 listen {{
  type = auth
  ipaddr = 192.0.2.2
  port = 1812
 }}
 authorize {{
  eap
 }}
 authenticate {{
  eap
 }}
 post-auth {{
  Post-Auth-Type REJECT {{
   update reply {{
    MS-MPPE-Recv-Key !* ANY
    MS-MPPE-Send-Key !* ANY
   }}
   eap
  }}
  update reply {{
   Tunnel-Type := VLAN
   Tunnel-Medium-Type := IEEE-802
   Tunnel-Private-Group-Id := "110"
  }}
 }}
}}
''')
 return dest

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--prefix',type=Path,default=Path('/'))
 a=p.parse_args();print(create(a.destination,a.prefix))
