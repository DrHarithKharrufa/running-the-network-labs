"""Read declared prerequisites. No installation or lab execution; no readiness guarantee."""
import argparse,importlib.metadata,json,os,platform,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def inspect(contract):
    missing=[];detected={};minimum=contract.get('python_min',[3,11])
    if tuple(sys.version_info[:2])<tuple(minimum):missing.append('Python '+'.'.join(map(str,minimum))+'+')
    if contract.get('os') and platform.system() not in contract['os']:missing.append('OS: '+', '.join(contract['os']))
    if contract.get('root') and not (hasattr(os,'geteuid') and os.geteuid()==0):missing.append('Linux root privileges')
    for binary in contract.get('binaries',[]):
        detected[binary]=shutil.which(binary)
        if not detected[binary]:missing.append('binary '+binary)
    for package,wanted in contract.get('packages',{}).items():
        try:version=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:version=None
        detected[package]=version
        if version!=wanted:missing.append(f'{package}=={wanted} (detected {version})')
    return {'missing':missing,'detected':detected,'manual':contract.get('manual',[]),
            'status':'MISSING' if missing else 'MANUAL_CHECK_REQUIRED' if contract.get('manual') or not contract.get('fully_declared',True) else 'DECLARED_PREREQUISITES_DETECTED'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--chapter',type=int)
    p.add_argument('--mode',choices=['offline','live'],default='offline');p.add_argument('--json',action='store_true');a=p.parse_args()
    manifest=json.loads((HERE/'prerequisites.json').read_text());chosen=manifest['labs']
    if a.chapter is not None:
        name=f'lab{a.chapter:02}'
        if name not in chosen:p.error('chapter has no lab directory')
        chosen={name:chosen[name]}
    results={}
    for name,modes in chosen.items():
        mode=modes[a.mode]
        if a.mode=='offline':
            programs=mode['test_programs']
            results[name]={k:inspect(manifest['tests'][k]) for k in programs} if programs else {'status':'NO_DECLARED_OFFLINE_TEST_PROGRAM'}
        else:results[name]=inspect(mode)
    report={'scope':'Detected declared prerequisites only. Does not prove a lab runs or qualifies a platform.',
            'python':sys.version,'platform':platform.platform(),'mode':a.mode,'labs':results}
    if a.json:print(json.dumps(report,indent=2))
    else:
        print(report['scope'])
        for name,result in results.items():print(name,json.dumps(result))
    return 0

if __name__=='__main__':raise SystemExit(main())
