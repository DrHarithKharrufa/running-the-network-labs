"""Two concurrent reads; report partial failure without inventing health."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from common import request, validate_snapshot


def collect(asset):
    return validate_snapshot(request('/api/devices/'+asset))


if __name__=='__main__':
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(collect,asset):asset for asset in ('r1','r2','missing')}
        for future in as_completed(jobs):
            asset=jobs[future]
            try:
                snapshot=future.result()
                results.append({'asset_id':asset,'status':'COLLECTED','state':snapshot})
            except Exception as error:
                results.append({'asset_id':asset,'status':'UNKNOWN','error_type':type(error).__name__})
    print(json.dumps(sorted(results,key=lambda row:row['asset_id']),indent=2))
    raise SystemExit(1 if any(row['status']=='UNKNOWN' for row in results) else 0)
