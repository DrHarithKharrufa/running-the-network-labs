#!/usr/bin/env python3
"""Optional local Batfish evidence collector. Does not upload, deploy or authorise promotion."""
import argparse
import importlib.metadata
import ipaddress
import json

def collect(session, headers_factory, network, snapshot, start, src, dst, sport, dport, expected_nodes):
    # set_network can create a missing network; deliberately do not call it.
    if network not in session.list_networks():
        raise ValueError('named network absent; create/upload explicitly using the server documentation')
    session.network = network
    session.set_snapshot(snapshot)
    queries = {
        'file_parse_status':session.q.fileParseStatus(),
        'initialisation_issues':session.q.initIssues(),
        'node_properties':session.q.nodeProperties(),
        'traceroute':session.q.traceroute(startLocation=start,
            headers=headers_factory(srcIps=src,dstIps=dst,ipProtocols=['TCP'],
                                    srcPorts=str(sport),dstPorts=str(dport)),ignoreFilters=False),
    }
    frames = {name:question.answer().frame() for name,question in queries.items()}
    nodes = {str(node) for node in frames['node_properties']['Node']}
    # Text exports retain model diagnostics and trace details without pretending
    # to normalise arbitrary versions of the service's table schemas.
    return {'status':'REVIEW_REQUIRED','network':network,'snapshot':snapshot,
            'server_versions':session.get_component_versions(),
            'expected_nodes':sorted(expected_nodes),'observed_nodes':sorted(nodes),
            'missing_nodes':sorted(set(expected_nodes)-nodes),
            'unexpected_nodes':sorted(nodes-set(expected_nodes)),
            'row_counts':{name:len(frame) for name,frame in frames.items()},
            'evidence_tables':{name:frame.to_string(index=False) for name,frame in frames.items()},
            'scope':'A directional model trace for one explicit TCP flow; not bidirectional connectivity, service health or a deployment gate. Review all diagnostics, model inputs and trace coverage. No promotion authorised.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true',help='query an already populated local analysis service')
    p.add_argument('--network');p.add_argument('--snapshot');p.add_argument('--start')
    p.add_argument('--src');p.add_argument('--dst')
    p.add_argument('--src-port',type=int);p.add_argument('--dst-port',type=int)
    p.add_argument('--expected-nodes',help='comma-separated complete expected node set')
    a=p.parse_args()
    if not a.run:
        print(json.dumps({'status':'NOT_RUN','reason':'supply --run and an explicit existing snapshot/flow; optional pybatfish dependency and local server required'}));return 1
    if not all([a.network,a.snapshot,a.start,a.src,a.dst,a.expected_nodes]) or a.src_port is None or a.dst_port is None:
        p.error('--run requires network, snapshot, start, src/dst, both ports and expected-nodes')
    try:
        for value in [a.src,a.dst]:ipaddress.IPv4Address(value)
        if not all(1<=port<=65535 for port in [a.src_port,a.dst_port]):raise ValueError('ports must be 1..65535')
        expected=[name.strip() for name in a.expected_nodes.split(',')]
        if not all(expected) or len(set(expected))!=len(expected):raise ValueError('expected-nodes must be non-empty and unique')
    except ValueError as e:p.error(str(e))
    try:
        from pybatfish.client.session import Session
        from pybatfish.datamodel.flow import HeaderConstraints
        # Loopback only. HTTP request timeout is not a whole-analysis deadline.
        bf=Session(host='127.0.0.1',timeout=30)
        result=collect(bf,HeaderConstraints,a.network,a.snapshot,a.start,a.src,a.dst,
                       a.src_port,a.dst_port,expected)
        result['client_version']=importlib.metadata.version('pybatfish')
        print(json.dumps(result,indent=2,default=str));return 1
    except Exception as e:
        print(json.dumps({'status':'ERROR','reason':f'{type(e).__name__}: {e}','promotion':'BLOCKED'}));return 2

if __name__=='__main__':raise SystemExit(main())
