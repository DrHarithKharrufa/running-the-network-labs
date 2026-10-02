"""OPS-12: interpret supplied offline cumulative counter observations."""
import csv,json,math
from pathlib import Path
def _calculate(row):
 if row['interface_before']!=row['interface_after']:return {'decision':'REFUSE','reason':'changed identity'}
 if row['discontinuity_before']!=row['discontinuity_after']:return {'decision':'REFUSE','reason':'reset/discontinuity'}
 seconds=float(row['seconds']);width=int(row['width_bits']);before=int(row['octets_before']);after=int(row['octets_after']);bound=float(row['max_bit_rate'])
 up_before=float(row['uptime_before']);up_after=float(row['uptime_after'])
 if not all(math.isfinite(x) for x in [seconds,bound,up_before,up_after]) or seconds<=0 or width not in (32,64) or bound<=0 or up_before<0 or up_after<0:return {'decision':'REFUSE','reason':'invalid units/interval/width/bound'}
 if up_after<up_before:return {'decision':'REFUSE','reason':'reset/discontinuity'}
 modulus=1<<width
 if not (0<=before<modulus and 0<=after<modulus):return {'decision':'REFUSE','reason':'counter outside width'}
 maximum_octets=bound*seconds/8
 if not math.isfinite(maximum_octets):return {'decision':'REFUSE','reason':'non-finite derived bound'}
 if maximum_octets>=modulus:return {'decision':'REFUSE','reason':'possible multiple wraps'}
 delta=(after-before)%modulus
 if delta>maximum_octets:return {'decision':'REFUSE','reason':'delta exceeds declared rate bound'}
 return {'decision':'VALID','octets_delta':delta,'average_bit_rate':8*delta/seconds,'units':'bit/s','wrap':after<before}
def calculate(row):
 try:return _calculate(row)
 except (ValueError,TypeError,KeyError,OverflowError):return {'decision':'REFUSE','reason':'malformed numeric/identity evidence'}
def main():
 rows=list(csv.DictReader((Path(__file__).parent/'COUNTER-WORKSHEET.csv').open(encoding='utf8')));results={r['case']:calculate(r) for r in rows}
 assert results['ordinary']['average_bit_rate']==2400
 assert results['bounded-wrap']['octets_delta']==296 and results['bounded-wrap']['average_bit_rate']==2368
 assert all(results[k]['decision']=='REFUSE' for k in ['reset','ambiguous-wrap','changed-interface'])
 for field in ['seconds','max_bit_rate','uptime_before','uptime_after']:
  for bad in ['nan','inf','-inf','not-a-number']:
   assert calculate({**rows[0],field:bad})['decision']=='REFUSE'
 print(json.dumps({'mode':'OFFLINE_WORKSHEET','results':results,'checks':21,'device_execution':False},indent=2,allow_nan=False))
if __name__=='__main__':main()
