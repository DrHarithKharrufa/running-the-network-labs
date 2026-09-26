"""Create a local draft case, inspect evidence, then make a separate decision."""
import argparse,json,time,uuid
from common import request

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case');p.add_argument('--decision',choices=['investigate','dismiss'])
    a=p.parse_args()
    if a.case:
        result=request('/cases/'+a.case)
        if a.decision:
            result=request('/cases/'+a.case+'/decision','POST',
                           {'decision':a.decision,'expected_revision':result['revision']})
    else:
        result=request('/events','POST',{'event_id':uuid.uuid4().hex,'sensor_id':'sensor-r1-eth2',
                       'status':'Down','observed_at':int(time.time()),'sequence':time.time_ns()//1000000})
        if 'case_id' in result:result=request('/cases/'+result['case_id'])
    print(json.dumps(result,indent=2))
