"""Offline conservative exposure graph. Edges mean MAY affect, not WILL fail.

Service populations must be disjoint. The graph omits route selection, redundant
path logic and timing, and is not a NOS, forwarding simulation or outage forecast.
"""
import json


def exposure(graph, changed, populations):
    if not isinstance(graph,dict) or not graph or not changed:
        raise ValueError('non-empty graph and changed-node set required')
    if any(not isinstance(k,str) or not k for k in graph):
        raise ValueError('named nodes required')
    if not set(changed) <= set(graph) or not set(populations) <= set(graph):
        raise ValueError('unknown changed node or service population')
    for neighbours in graph.values():
        if not isinstance(neighbours,(list,tuple,set)) or not set(neighbours) <= set(graph):
            raise ValueError('dependency outside declared graph')
    if any(type(n) is not int or n <= 0 for n in populations.values()):
        raise ValueError('positive integer, disjoint service populations required')
    if not populations:
        raise ValueError('service population must not be empty')
    seen, pending = set(), list(changed)
    while pending:
        node=pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(graph[node])
    services=sorted(seen & set(populations))
    total=sum(populations.values())
    exposed=sum(populations[k] for k in services)
    return {'potential_services':services,'potential_population':exposed,
            'population_total':total,'exposure_fraction':exposed/total,
            'reachable_nodes':sorted(seen)}


def fixture():
    edges=[f'edge-{i:02d}' for i in range(1,41)]
    graph={'rr-A':edges.copy(),'rr-B':edges.copy()}
    populations={}
    for n in edges:
        service='service-'+n[-2:]
        graph[n]=[service]
        graph[service]=[]
        populations[service]=1000
    return graph,populations


def demo():
    graph,populations=fixture()
    narrowed={k:list(v) for k,v in graph.items()}
    narrowed['rr-A']=['edge-01']  # Assumed verified scope control, not implemented by this model.
    cases={
        'one edge':exposure(graph,['edge-01'],populations),
        'one shared route reflector':exposure(graph,['rr-A'],populations),
        'reflector with assumed scope control':exposure(narrowed,['rr-A'],populations),
    }
    return {'scope':'offline potential exposure, not observed outage',
            'router_count':42,'cases':{k:{x:v for x,v in e.items() if x not in ['reachable_nodes','potential_services']} for k,e in cases.items()}}


if __name__=='__main__':
    print(json.dumps(demo(),indent=2))
