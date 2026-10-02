"""Generate bounded synthetic PCAP fixtures offline. Never transmits packets."""
import argparse,hashlib,ipaddress,json,struct,time
from pathlib import Path
def mac(text):
 value=bytes.fromhex(text.replace(':',''))
 if len(value)!=6:raise ValueError('MAC must contain six octets')
 return value
def pcap(path,packets):
 if path.exists():raise ValueError('refuse to overwrite existing packet evidence')
 with path.open('wb') as f:
  f.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
  for i,p in enumerate(packets):f.write(struct.pack('<IIII',1700000000,i*100000,len(p),len(p))+p)
def ethernet(src,dst,kind,payload):return mac(dst)+mac(src)+struct.pack('!H',kind)+payload
def ipv6(src,dst,next_header,payload,hop=8):
 return struct.pack('!IHBB',6<<28,len(payload),next_header,hop)+ipaddress.IPv6Address(src).packed+ipaddress.IPv6Address(dst).packed+payload
def classic_end(src_mac,dst_mac,src_ip,local_sid,next_sid,segments_left):
 # LastEntry1: wire Segment List[0]=next, [1]=local; active outerDA=local.
 # NonzeroSL valid End; SL0 precisely invalid for plain End without a flavor.
 srh=struct.pack('!BBBBBBH',59,4,4,segments_left,1,0,0)+ipaddress.IPv6Address(next_sid).packed+ipaddress.IPv6Address(local_sid).packed
 return ethernet(src_mac,dst_mac,0x86dd,ipv6(src_ip,local_sid,43,srh))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',choices=['ce-five','wjh-source-multicast','classic-end'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--src-mac',default='02:00:00:00:01:01');p.add_argument('--dst-mac',default='02:00:00:00:02:02');p.add_argument('--source-ip',default='2001:db8:ffff::1');p.add_argument('--local-sid',default='2001:db8:1:1::100');p.add_argument('--next-sid',default='2001:db8:3:3::100');a=p.parse_args()
 if a.kind=='ce-five':packets=[ethernet(a.src_mac,a.dst_mac,0x88b5,(f'WB-DC04-{i:02}').encode().ljust(46,b'\0')) for i in range(1,6)]
 elif a.kind=='wjh-source-multicast':packets=[ethernet('01:00:5e:00:00:01',a.dst_mac,0x88b5,(f'WB-OPS05-{i:02}').encode().ljust(46,b'\0')) for i in range(1,6)]
 else:packets=[classic_end(a.src_mac,a.dst_mac,a.source_ip,a.local_sid,a.next_sid,sl) for sl in (1,0)]
 if a.out.exists() or a.out.with_suffix('.manifest.json').exists():raise ValueError('refuse to overwrite packet evidence or its provenance')
 a.out.parent.mkdir(parents=True,exist_ok=True);pcap(a.out,packets)
 manifest={'mode':'SYNTHETIC_OFFLINE_PACKET_FIXTURE','kind':a.kind,'packet_count':len(packets),'packet_lengths':[len(x) for x in packets],'ethernet_fcs_included':False,'minimum_frame_padding':'CE/WJH frames padded to 60 bytes before FCS; SRv6 frames larger','pcap_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'device_execution':False,'generated_packets_are_not_captures':True}
 if a.kind=='classic-end':manifest.update(local_sid=a.local_sid,next_sid=a.next_sid,source_ip=a.source_ip,hop_limit=8,last_entry=1,segments_left=[1,0],wire_segment_list=[a.next_sid,a.local_sid],next_header=59,expected_valid_transform={'outer_destination':a.next_sid,'segments_left':0,'hop_limit':7},invalid_condition='SL0 at plain End; do not generalize to USD/USP/PSP or compressed uN')
 if a.kind=='wjh-source-multicast':manifest.update(source_mac='01:00:5e:00:00:01',expected_reason_id=209,expected_reason='Source MAC is multicast',not_an_acl_drop=True)
 a.out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
