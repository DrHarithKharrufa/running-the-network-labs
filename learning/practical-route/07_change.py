"""Local simulator only: explicit apply, read-back, service check and recovery."""
import argparse
import importlib
import json
from common import request, validate_snapshot
plan=importlib.import_module('05_plan').plan


def execute(description, apply=False, fail_service=False):
    before=validate_snapshot(request('/api/devices/r1'))
    proposal=plan(before,description)
    if not apply or not proposal['change_required']:
        return {'status':'DRY_RUN' if not apply else 'NO_CHANGE','plan':proposal}
    try:
        ack=request('/api/devices/r1','PUT',{'description':description,
                    'expected_generation':before['generation']})
    except Exception:
        # A lost response does not justify repeating the write.
        try: observed=request('/api/devices/r1')
        except Exception: observed=None
        return {'status':'UNKNOWN_WRITE','observed':observed,'plan':proposal}
    try:
        observed=validate_snapshot(request('/api/devices/r1'))
    except Exception:
        return {'status':'UNKNOWN_VERIFICATION','plan':proposal}
    if observed['generation']!=ack['generation'] or observed['description']!=description:
        return {'status':'CONCURRENT_OR_UNVERIFIED','observed':observed}
    try:
        service=request('/api/service')
        if type(service.get('healthy')) is not bool: raise ValueError('invalid service observation')
    except Exception:
        return {'status':'UNKNOWN_SERVICE','observed':observed}
    if service['healthy'] and not fail_service:
        return {'status':'VERIFIED','generation':observed['generation'],'service':service}
    try:
        restored=request('/api/devices/r1','PUT',{'description':before['description'],
                          'expected_generation':observed['generation']})
        check=validate_snapshot(request('/api/devices/r1'))
        ok=check['description']==before['description'] and check['generation']==restored['generation']
        recovery_service=request('/api/service')
        if type(recovery_service.get('healthy')) is not bool:
            raise ValueError('invalid recovery service observation')
        status=('RECOVERY_UNVERIFIED' if not ok else
                'ROLLED_BACK' if recovery_service['healthy'] else 'RECOVERY_SERVICE_FAILED')
        return {'status':status,'service':recovery_service,'restored':check}
    except Exception:
        return {'status':'RECOVERY_UNKNOWN','plan':proposal}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--description',default='Aldergate verified uplink')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--fail-service',action='store_true',help='constructed failed acceptance check')
    args=parser.parse_args()
    result=execute(args.description,args.apply,args.fail_service)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'] in ('DRY_RUN','NO_CHANGE','VERIFIED','ROLLED_BACK') else 1)
