"""Loopback teaching API. Device data is simulated; HTTP and SQLite are real.

Run with a new --db path for a clean exercise. Set RTN_LAB_TOKEN first.
No production targets, external notification or containment operation exists.
"""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.parse import parse_qs
from common import validate_snapshot


class Problem(Exception):
    def __init__(self,status,message): self.status,self.message=status,message


class Store:
    def __init__(self,path):
        self.path=str(path)
        self.lock=threading.RLock()
        self.fault='none'
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sensor_order(sensor TEXT PRIMARY KEY, sequence INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            ''')
            base=json.loads(Path(__file__).with_name('snapshot.json').read_text())
            for asset in ('r1','r2','r3'):
                state={**base,'asset_id':asset}
                db.execute('INSERT OR IGNORE INTO devices VALUES (?,?)',(asset,json.dumps(state)))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=3)
        try:
            with db:
                yield db
        finally:
            db.close()

    def device(self,asset):
        with self.connect() as db:
            row=db.execute('SELECT state FROM devices WHERE id=?',(asset,)).fetchone()
        if row is None: raise Problem(404,'unknown asset')
        return json.loads(row[0])

    def change(self,asset,data):
        if set(data)!={'description','expected_generation'} or type(data['expected_generation']) is not int:
            raise Problem(400,'expected description and integer generation')
        if not isinstance(data['description'],str) or not 1<=len(data['description'])<=80:
            raise Problem(400,'invalid description')
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT state FROM devices WHERE id=?',(asset,)).fetchone()
            if row is None: raise Problem(404,'unknown asset')
            state=json.loads(row[0])
            if state['generation']!=data['expected_generation']: raise Problem(409,'generation conflict')
            state['description']=data['description'];state['generation']+=1
            db.execute('UPDATE devices SET state=? WHERE id=?',(json.dumps(state),asset))
        return state

    def event(self,data,now=None):
        now=time.time() if now is None else now
        fields={'event_id','sensor_id','status','observed_at','sequence'}
        if not isinstance(data,dict) or set(data)!=fields: raise Problem(400,'unexpected event fields')
        for key in ('event_id','sensor_id'):
            if not isinstance(data[key],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',data[key]):
                raise Problem(400,'invalid identifier')
        if data['sensor_id']!='sensor-r1-eth2': raise Problem(404,'sensor has no approved owner mapping')
        if data['status'] not in ('Down','Up'): raise Problem(400,'invalid status')
        if type(data['sequence']) is not int or not 0<=data['sequence']<2**53:
            raise Problem(400,'invalid sequence')
        if type(data['observed_at']) not in (int,float) or not 0<=data['observed_at']<=now+30:
            raise Problem(400,'invalid or future timestamp')
        fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with self.lock,self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT fingerprint,result FROM events WHERE id=?',(data['event_id'],)).fetchone()
            if prior:
                if prior[0]!=fingerprint: raise Problem(409,'event ID reused with different content')
                return {**json.loads(prior[1]),'duplicate':True}
            order=db.execute('SELECT sequence FROM sensor_order WHERE sensor=?',(data['sensor_id'],)).fetchone()
            stale=(now-data['observed_at']>300 or order is not None and data['sequence']<=order[0])
            if stale:
                result={'status':'STALE','event_id':data['event_id'],'duplicate':False}
            else:
                if self.fault=='unavailable': raise Problem(503,'diagnostic collector unavailable; retry same event')
                snapshot=self.device('r1')
                if self.fault=='malformed': snapshot={'interfaces':[]}
                try: validate_snapshot(snapshot)
                except ValueError as exc: raise Problem(502,'diagnostic response invalid') from exc
                evidence={'id':'ev-'+data['event_id'],'asset_id':'r1','interface':'eth2',
                          'collected_at':now,'scope':'local simulated device', 'snapshot':snapshot}
                cid='case-'+data['event_id']
                row={'case_id':cid,'revision':1,'status':'AWAITING_REVIEW','owner':'branch-team',
                     'event':data,'evidence':[evidence],
                     'summary':'Monitoring reported '+data['status']+'. Collected eth2 state is '+
                                snapshot['interfaces'][1]['oper_state']+'. Cause is not established.',
                     'suggested_check':'Compare interface state, peer state and recent authorised changes.',
                     'ai_status':'NOT_REQUESTED','decisions':[]}
                db.execute('INSERT INTO cases VALUES (?,?)',(cid,json.dumps(row)))
                db.execute('INSERT INTO sensor_order VALUES (?,?) ON CONFLICT(sensor) DO UPDATE SET sequence=excluded.sequence',
                           (data['sensor_id'],data['sequence']))
                result={'status':'DRAFT_CREATED','event_id':data['event_id'],'case_id':cid,'duplicate':False}
            db.execute('INSERT INTO events VALUES (?,?,?)',(data['event_id'],fingerprint,json.dumps(result)))
        return result

    def case(self,cid):
        with self.connect() as db:
            row=db.execute('SELECT body FROM cases WHERE id=?',(cid,)).fetchone()
        if row is None: raise Problem(404,'unknown case')
        return json.loads(row[0])

    def decide(self,cid,data):
        if set(data)!={'decision','expected_revision'} or data['decision'] not in ('investigate','dismiss'):
            raise Problem(400,'invalid decision')
        if type(data['expected_revision']) is not int: raise Problem(400,'invalid revision')
        with self.lock,self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT body FROM cases WHERE id=?',(cid,)).fetchone()
            if row is None: raise Problem(404,'unknown case')
            case=json.loads(row[0])
            if case['revision']!=data['expected_revision'] or case['status']!='AWAITING_REVIEW':
                raise Problem(409,'case changed or already reviewed')
            case['status']='REVIEWED' if data['decision']=='investigate' else 'DISMISSED'
            case['revision']+=1
            case['decisions'].append({'decision':data['decision'],'reviewer':'local-token-holder','time':time.time()})
            db.execute('UPDATE cases SET body=? WHERE id=?',(json.dumps(case),cid))
        return case


def handler(store,token):
    class Handler(BaseHTTPRequestHandler):
        server_version='RTN-Lab/1'
        def log_message(self,*args): pass  # Do not log headers, tokens or event text.
        def send(self,status,data):
            raw=json.dumps(data,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def handle_call(self):
            try:
                if self.command!='GET':
                    if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token):
                        raise Problem(401,'invalid local credential')
                    try: length=int(self.headers.get('Content-Length','0'))
                    except ValueError: raise Problem(400,'invalid length')
                    if not 1<=length<=8192: raise Problem(413,'body must contain 1 to 8192 bytes')
                    raw=self.rfile.read(length).decode('utf-8')
                    if self.headers.get_content_type()=='application/x-www-form-urlencoded':
                        fields=parse_qs(raw,strict_parsing=True)
                        if any(len(v)!=1 for v in fields.values()): raise Problem(400,'duplicate form field')
                        data={k:v[0] for k,v in fields.items()}
                        for key in ('observed_at','sequence'):
                            if key in data:data[key]=int(data[key])
                    elif self.headers.get_content_type()=='application/json':
                        data=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite number')))
                    else: raise Problem(415,'expected JSON or form data')
                    if not isinstance(data,dict): raise Problem(400,'expected object')
                if self.path=='/health' and self.command=='GET': result={'status':'READY','scope':'local simulator'}
                elif self.path=='/api/service' and self.command=='GET':
                    result={'healthy':True,'scope':'independent local HTTP acceptance endpoint; simulated service health'}
                elif re.fullmatch('/api/devices/r[123]',self.path):
                    asset=self.path.rsplit('/',1)[1]
                    if self.command=='GET': result=store.device(asset)
                    elif self.command=='PUT': result=store.change(asset,data)
                    else: raise Problem(405,'method not allowed')
                elif self.path=='/events' and self.command=='POST': result=store.event(data)
                elif re.fullmatch('/cases/case-[A-Za-z0-9_-]{1,64}',self.path) and self.command=='GET':
                    result=store.case(self.path.rsplit('/',1)[1])
                elif re.fullmatch('/cases/case-[A-Za-z0-9_-]{1,64}/decision',self.path) and self.command=='POST':
                    result=store.decide(self.path.split('/')[2],data)
                elif self.path=='/lab/fault' and self.command=='POST':
                    if set(data)!={'collector'} or data['collector'] not in ('none','unavailable','malformed'):
                        raise Problem(400,'unknown fault')
                    store.fault=data['collector'];result={'collector':store.fault}
                else: raise Problem(404,'unknown operation')
                self.send(200,result)
            except Problem as exc:self.send(exc.status,{'error':exc.message})
            except (ValueError,UnicodeError):self.send(400,{'error':'malformed input'})
            except sqlite3.Error:self.send(503,{'error':'journal unavailable'})
        do_GET=handle_call
        do_POST=handle_call
        do_PUT=handle_call
        def setup(self):
            super().setup();self.connection.settimeout(5)
    return Handler


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--db',default='rtn-lab.sqlite')
    parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    token=os.environ.get('RTN_LAB_TOKEN','')
    if len(token)<24:raise SystemExit('Set RTN_LAB_TOKEN to at least 24 random characters; do not publish it.')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(Store(args.db),token))
    print(f'RTN lab listening on 127.0.0.1:{args.port}; simulated device state; Ctrl+C stops.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
