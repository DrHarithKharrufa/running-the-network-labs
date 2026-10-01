"""Count semantic records from FRR10.5 show ip ospf database json."""
import json,sys
from pathlib import Path

def count(data):
    result={}
    groups={'routerLinkStates':'1-router','networkLinkStates':'2-network',
            'summaryLinkStates':'3-summary','asbrSummaryLinkStates':'4-ASBR-summary',
            'asExternalLinkStates':'5-external','nssaExternalLinkStates':'7-NSSA'}
    def visit(obj,scope):
        for key,value in obj.items():
            if key=='areas':
                for area,contents in value.items():visit(contents,'area '+area)
            elif key in groups and isinstance(value,list):
                result[scope+' / '+groups[key]]=sum(int(row.get('lsaAge',0))<3600 for row in value)
    visit(data,'AS')
    return result

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 count-lsas.py database.json')
    result=count(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps({'non_maxage_record_counts':result,'total':sum(result.values()),
       'scope':'Base OSPFv2 types 1/2/3/4/5/7, excluding reported MaxAge; not opaque extensions, memory or SPF work.'},indent=2))
