"""Small, explicit contracts shared by the practical route (Python 3.11+)."""
import json
import os
from urllib.request import Request, build_opener, HTTPRedirectHandler

BASE = 'http://127.0.0.1:8765'  # Deliberately fixed local teaching service.
LIMIT = 65536


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('local teaching API must not redirect')


def request(path, method='GET', data=None, timeout=3):
    if not path.startswith('/') or path.startswith('//') or '\\' in path:
        raise ValueError('expected a local API path')
    headers={'Accept':'application/json'}
    if data is not None:
        headers['Content-Type']='application/json'
    if method!='GET':
        token=os.environ.get('RTN_LAB_TOKEN')
        if not token: raise ValueError('set RTN_LAB_TOKEN from your local server startup')
        headers['Authorization']='Bearer '+token
    req=Request(BASE+path, data=None if data is None else json.dumps(data).encode(),
                headers=headers, method=method)
    with build_opener(NoRedirect()).open(req,timeout=timeout) as response:
        if response.headers.get_content_type()!='application/json':
            raise ValueError('response is not JSON')
        raw=response.read(LIMIT+1)
        if len(raw)>LIMIT: raise ValueError('response too large')
    result=json.loads(raw)
    if not isinstance(result,dict): raise ValueError('expected an object')
    return result


def validate_snapshot(value, expected=('eth1','eth2')):
    if not isinstance(value,dict) or not isinstance(value.get('interfaces'),list):
        raise ValueError('missing interface list')
    if type(value.get('generation')) is not int or value['generation']<0:
        raise ValueError('invalid generation')
    names=[]
    for row in value['interfaces']:
        if not isinstance(row,dict) or set(row)!= {'name','oper_state','errors','packets'}:
            raise ValueError('invalid interface fields')
        if row['oper_state'] not in ('up','down'): raise ValueError('invalid state')
        if any(type(row[k]) is not int or row[k]<0 for k in ('errors','packets')):
            raise ValueError('invalid counter')
        names.append(row['name'])
    if len(names)!=len(set(names)) or set(names)!=set(expected):
        raise ValueError('missing, duplicate or unexpected interface')
    return value
