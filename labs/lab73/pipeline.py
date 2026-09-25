#!/usr/bin/env python3
"""Executable local policy gate; unavailable analysis/deployment stages remain NOT_RUN."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from policy import check, PROFILE

def run(current, candidate):
    return {'scope':'Local policy profile only; no analysis service, device or deployment called',
            'profile':PROFILE,
            'artefact_hashes':{name:hashlib.sha256(value.encode('utf-8')).hexdigest() for name,value in [('current',current),('candidate',candidate)]},
            'stages':{'current_policy':check(current),'candidate_policy':check(candidate),
                      'batfish':{'status':'NOT_RUN'},'NOS_integration':{'status':'NOT_RUN'},
                      'service_canary':{'status':'NOT_RUN'},'deployment':{'status':'NOT_RUN'}},
            'promotion':'BLOCKED: required integration, release authorisation and service evidence absent'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current',type=Path);parser.add_argument('--candidate',type=Path)
    parser.add_argument('--demo-original',action='store_true')
    args=parser.parse_args()
    if args.demo_original:
        print('HISTORICAL FLAWED DEMO: no Batfish, canary or deployment actually ran.')
        runpy.run_path(str(Path(__file__).with_name('original_pipeline.py')),run_name='__main__');return 0
    if bool(args.current)!=bool(args.candidate):parser.error('supply both current and candidate, or neither for synthetic demo')
    fixture=Path(__file__).parent/'fixtures/good.cfg'
    current=(args.current or fixture).read_text('utf-8');candidate=(args.candidate or fixture).read_text('utf-8')
    print(json.dumps(run(current,candidate),indent=2))
    return 1  # absent required gates never become promotion success

if __name__=='__main__':raise SystemExit(main())
