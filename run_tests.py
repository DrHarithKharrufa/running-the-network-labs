"""Run declared tests and retain logs. --quick never guesses from nearby topologies."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import environment_check
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--quick',action='store_true')
    p.add_argument('--include-live',action='store_true');p.add_argument('--timeout',type=int,default=300)
    p.add_argument('--out',type=Path,default=Path('test-results'));a=p.parse_args()
    if a.quick and a.include_live:p.error('choose quick or include-live')
    a.out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((HERE/'prerequisites.json').read_text())['tests']
    found={q.relative_to(HERE).as_posix() for top in ['labs','learning','harness'] for q in (HERE/top).rglob('test_*.py')}
    if found!=set(manifest):p.error('test inventory differs from explicit prerequisite manifest')
    results=[]
    for path,contract in sorted(manifest.items()):
        file=HERE/path;check=environment_check.inspect(contract)
        row={'path':path,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'prerequisites':check}
        if contract['kind']=='live' and not a.include_live:row.update(status='NOT_RUN',reason='live test not selected')
        elif check['missing']:row.update(status='NOT_RUN',reason='missing declared prerequisites')
        else:
            start=time.monotonic();log=path.replace('/','__')+'.log'
            try:
                r=subprocess.run([sys.executable,'-B',file.name],cwd=file.parent,capture_output=True,
                    text=True,encoding='utf-8',errors='replace',timeout=a.timeout,env={**os.environ,'PYTHONUTF8':'1'})
                content=r.stdout+r.stderr
                status='PASS_WITH_SKIPS' if r.returncode==0 and ('skipped=' in content or 'SKIP' in content) else 'PASS' if r.returncode==0 else 'FAIL'
                row.update(status=status,returncode=r.returncode,seconds=round(time.monotonic()-start,3),log=log)
            except subprocess.TimeoutExpired as error:
                content=str(error);row.update(status='TIMEOUT',log=log)
            (a.out/log).write_text(content,encoding='utf-8')
        results.append(row)
        (a.out/'execution.json').write_text(json.dumps({'python':sys.version,'results':results},indent=2))
        print(path,row['status'],flush=True)
    counts={status:sum(r['status']==status for r in results) for status in sorted({r['status'] for r in results})}
    print(json.dumps(counts))
    return 1 if any(r['status'] in ('FAIL','TIMEOUT') for r in results) else 0

if __name__=='__main__':raise SystemExit(main())
