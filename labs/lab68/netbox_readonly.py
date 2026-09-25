#!/usr/bin/env python3
"""Read-only NetBox 4.3.7 API illustration, offline fixtures by default.

--live requires an explicit HTTPS interfaces URL and NETBOX_TOKEN. Never sends a
write request; rejects redirects and cross-origin pagination before sending tokens.
Pagination is not an atomic database snapshot. See README for release and scope.
"""
import argparse,json,os,ssl
from pathlib import Path
from urllib.parse import urlparse,urljoin
from urllib.request import Request,HTTPSHandler,HTTPRedirectHandler,build_opener

START='https://netbox.example/api/dcim/interfaces/?device_id=1&limit=1&ordering=id'

def checked_url(url,origin):
    u=urlparse(url);base=urlparse(origin)
    if u.scheme!='https' or u.username or u.password or u.fragment:raise ValueError('HTTPS URL without credentials or fragment required')
    if not u.hostname or (u.hostname,u.port or 443)!=(base.hostname,base.port or 443):raise ValueError('Cross-origin pagination rejected')
    if u.path!='/api/dcim/interfaces/':raise ValueError('This client reads only the interfaces list endpoint')
    return url

def read_pages(start,fetch,max_pages=100):
    if type(max_pages) is not int or max_pages<1:raise ValueError('Invalid page bound')
    url=checked_url(start,start);visited=set();ids=set();rows=[];count=None
    while url:
        checked_url(url,start)
        if url in visited or len(visited)>=max_pages:raise ValueError('Pagination cycle or bound reached')
        visited.add(url);page=fetch(url)
        if type(page.get('count')) is not int or page['count']<0 or not isinstance(page.get('results'),list):raise ValueError('Invalid page envelope')
        if count is None:count=page['count']
        if page['count']!=count:raise ValueError('Count changed during pagination; recollect')
        for row in page['results']:
            if not isinstance(row,dict) or type(row.get('id')) is not int or row['id'] in ids:raise ValueError('Missing or repeated object ID')
            ids.add(row['id']);rows.append(row)
        nxt=page.get('next')
        if nxt is not None and (not isinstance(nxt,str) or not nxt):raise ValueError('Invalid next URL')
        url=checked_url(urljoin(url,nxt),start) if nxt is not None else None
    if len(rows)!=count:raise ValueError('Pagination count mismatch')
    return rows

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError('Redirect rejected; verify the canonical URL')

def live_fetcher(token):
    if not token or any(c.isspace() for c in token):raise ValueError('Token missing or malformed')
    opener=build_opener(HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
    def fetch(url):
        req=Request(url,headers={'Authorization':'Token '+token,'Accept':'application/json'},method='GET')
        with opener.open(req,timeout=10) as response:
            body=response.read(2_000_001)
            if len(body)>2_000_000:raise ValueError('Response exceeds teaching-client size bound')
            return json.loads(body)
    return fetch

def fixture_fetcher():
    bundle=json.loads(Path(__file__).with_name('api-fixtures.json').read_text('utf-8'))
    return lambda url:bundle['pages'][url]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',metavar='HTTPS_URL');args=parser.parse_args()
    start=args.live or START
    fetch=live_fetcher(os.environ.get('NETBOX_TOKEN','')) if args.live else fixture_fetcher()
    rows=read_pages(start,fetch)
    print(json.dumps({'scope':'live read-only GET' if args.live else 'synthetic API fixtures; no NetBox server executed',
                      'documentation_target':'NetBox 4.3.7','interfaces':rows},indent=2))

if __name__=='__main__':main()
