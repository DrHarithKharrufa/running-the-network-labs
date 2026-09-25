#!/usr/bin/env python3
"""
Build a GNS3 project from a Containerlab topology file.

The book keeps ONE topology definition per reference network, in
labs/topologies/*.clab.yml.  Containerlab consumes it directly.  This script
consumes supported node/link fields and creates a GNS3 wiring skeleton.
It does not translate startup configuration, binds, exec or launch semantics.

GNS3 has no notion of "pull this image"; every node must map to a template you
have already imported, using an appliance image you are licensed to run.  That
mapping lives in a template map file -- see template-map.example.yml.

    python3 gns3_build.py \
        --topology ../topologies/kestrel.clab.yml \
        --map      template-map.yml \
        --server   http://localhost:3080 \
        --project  kestrel

    # see what it would do, without touching the server
    python3 gns3_build.py -t ../topologies/kestrel.clab.yml -m template-map.yml --dry-run

Written for the GNS3 2.2-style controller API; not runtime-tested in this review.
No v3 path is implemented. Validate API/auth and templates
on an isolated compatible controller before use.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, sys, urllib.request, urllib.error

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required:  pip install pyyaml")


# --------------------------------------------------------------------------
# Topology parsing
# --------------------------------------------------------------------------
def load_topology(path):
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or not isinstance(doc.get('topology'), dict):
        raise ValueError('topology must be a mapping')
    topo = doc["topology"]
    if not isinstance(topo.get('nodes'), dict) or not topo['nodes']:
        raise ValueError('nodes must be a non-empty mapping')
    if topo.get('defaults') or topo.get('groups'):
        raise ValueError('defaults/groups are not translated; expand nodes explicitly')
    kinds = topo.get("kinds", {})
    nodes = {}
    for name, spec in topo["nodes"].items():
        spec = spec or {}
        if not isinstance(name,str) or not name or ':' in name or not isinstance(spec,dict):
            raise ValueError('invalid node name or specification')
        kind = spec.get("kind", "linux")
        merged = dict(kinds.get(kind, {}))
        merged.update(spec)
        merged["kind"] = kind
        nodes[name] = merged
    links = []
    for link in topo.get("links", []):
        if not isinstance(link,dict) or set(link)!={'endpoints'} or not isinstance(link['endpoints'],list) or len(link['endpoints'])!=2:
            raise ValueError('only two-endpoint links without additional properties are supported')
        a, b = link["endpoints"]
        if not all(isinstance(x,str) and x.count(':')==1 for x in [a,b]):
            raise ValueError('endpoint must be node:interface')
        an, ai = a.split(":", 1)
        bn, bi = b.split(":", 1)
        links.append(((an, ai), (bn, bi)))
    return doc.get("name", "lab"), nodes, links


def iface_index(iface):
    """Turn an interface name into an ordinal: e1-49 -> 49, eth2 -> 2, et7 -> 7."""
    match=re.fullmatch(r'(?:e1-|eth|et)([0-9]+)',iface)
    if not match:
        raise ValueError(f'{iface!r} requires an explicit port_map; breakout/slot indices cannot be inferred')
    return int(match[1])


def resolve_port(iface, rule):
    """Map a containerlab interface name onto a GNS3 (adapter, port) pair.

    scheme 'port'    : one adapter, many ports   (most Docker and IOU nodes)
    scheme 'adapter' : many adapters, one port   (most QEMU appliances)
    """
    def integer(value,label):
        if type(value) is not int or value<0:raise ValueError(f'{label} must be a non-negative integer')
        return value
    explicit=rule.get('port_map',{})
    if not isinstance(explicit,dict):raise ValueError('port_map must be a mapping')
    if iface in explicit:
        pair=explicit[iface]
        if not isinstance(pair,list) or len(pair)!=2:raise ValueError('port_map entry must be [adapter, port]')
        return tuple(integer(v,'adapter/port') for v in pair)
    if explicit:raise ValueError(f'{iface}: missing explicit port_map entry')
    scheme=rule.get('scheme','adapter')
    if scheme not in ['adapter','port']:raise ValueError('scheme must be adapter or port')
    idx = iface_index(iface) - integer(rule.get("first_index", 1),'first_index')
    if idx < 0:
        raise ValueError(f"{iface}: index below first_index for this template")
    idx += integer(rule.get("offset", 0),'offset')
    if scheme == "port":
        return 0, idx
    return idx, 0


def plan_wiring(nodes,links,tmap):
    """Validate all local mappings before any controller mutation.

    This cannot establish that a remote template exposes the mapped ports.
    """
    if not isinstance(tmap,dict):raise ValueError('template map must be a mapping')
    by_node=tmap.get('nodes',{}) or {};by_kind=tmap.get('kinds',{}) or {}
    rules={}
    for name,spec in nodes.items():
        rule=by_node.get(name,by_kind.get(spec['kind']))
        if not isinstance(rule,dict) or not isinstance(rule.get('template'),str) or not rule['template'].strip():
            raise ValueError(f'{name}: missing template mapping')
        rules[name]=rule
    used=set();ports=set();planned=[]
    for link in links:
        pair=[]
        for name,iface in link:
            if name not in nodes or not iface:raise ValueError(f'unknown or empty endpoint {name}:{iface}')
            if (name,iface) in used:raise ValueError(f'endpoint reused: {name}:{iface}')
            used.add((name,iface));adapter,port=resolve_port(iface,rules[name])
            if (name,adapter,port) in ports:raise ValueError(f'two interfaces map to the same target port on {name}')
            ports.add((name,adapter,port));pair.append((name,adapter,port))
        if pair[0][0]==pair[1][0]:raise ValueError('self-links are outside this helper scope')
        planned.append(pair)
    return rules,planned


# --------------------------------------------------------------------------
# Minimal GNS3 REST client
# --------------------------------------------------------------------------
class GNS3:
    def __init__(self, base, api="v2", token=None, dry_run=False):
        self.base = base.rstrip("/")
        self.api = api
        self.token = token
        self.dry_run = dry_run

    def _call(self, method, path, body=None):
        url = f"{self.base}/{self.api}{path}"
        if self.dry_run and method != "GET":
            print(f"  [dry-run] {method} {url}")
            if body:
                print("            " + json.dumps(body))
            identity=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()[:16]
            return {"node_id": f"dry-{identity}", "ports": []}
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            sys.exit(f"GNS3 API {method} {path} failed: {exc.code} {exc.read().decode()[:400]}")
        except urllib.error.URLError as exc:
            sys.exit(f"cannot reach the GNS3 controller at {self.base}: {exc.reason}")

    def templates(self):
        rows=self._call("GET", "/templates")
        if len({t['name'] for t in rows})!=len(rows):raise ValueError('ambiguous duplicate template names')
        return {t["name"]: t for t in rows}

    def create_project(self, name):
        return self._call("POST", "/projects", {"name": name})

    def add_node(self, project_id, template_id, name, x, y, compute_id='local'):
        return self._call(
            "POST", f"/projects/{project_id}/templates/{template_id}",
            {"x": int(x), "y": int(y), "compute_id": compute_id, "name": name})

    def add_link(self, project_id, a, b):
        return self._call("POST", f"/projects/{project_id}/links", {"nodes": [a, b]})


# --------------------------------------------------------------------------
# Layout: a plain circle keeps large topologies readable and needs no solver
# --------------------------------------------------------------------------
def circle_layout(names, radius=340):
    out, n = {}, len(names)
    for i, name in enumerate(sorted(names)):
        angle = 2 * math.pi * i / n
        out[name] = (radius * math.cos(angle), radius * math.sin(angle))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-t", "--topology", required=True)
    ap.add_argument("-m", "--map", required=True)
    ap.add_argument("-s", "--server", default="http://localhost:3080")
    ap.add_argument("-p", "--project")
    ap.add_argument("--api", default="v2", choices=["v2"],help='Only the documented 2.2-style path is implemented; no v3 compatibility claim')
    ap.add_argument('--compute-id',default='local',help='Actual target compute identifier; verify on your controller')
    ap.add_argument("--token")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lab_name, nodes, links = load_topology(args.topology)
    with open(args.map, encoding="utf-8") as fh:
        tmap = yaml.safe_load(fh)
    rules,planned=plan_wiring(nodes,links,tmap)
    rule_for=rules.__getitem__

    gns = GNS3(args.server, args.api, args.token, args.dry_run)

    print(f"topology : {args.topology}")
    print(f"nodes    : {len(nodes)}   links: {len(links)}")
    print('WIRING ONLY: startup-config, binds, exec, images, management and NOS syntax are not translated.')
    print('Local preflight does not validate remote template ports; verify the endpoint worksheet before creation.')

    available = {} if args.dry_run else gns.templates()
    missing = sorted({rule_for(n)["template"] for n in nodes
                      if not args.dry_run and rule_for(n)["template"] not in available})
    if missing:
        print("\nThese GNS3 templates are not imported on this controller:")
        for m in missing:
            print(f"  - {m}")
        sys.exit("\nImport the appliances first, or adjust the template map.")

    project = gns.create_project(args.project or lab_name)
    pid = 'dry-project' if args.dry_run else project.get('project_id')
    if not pid:raise RuntimeError('controller response lacks project_id; inspect partial creation before retry')
    print(f"project  : {args.project or lab_name}  ({pid})\n")

    pos = circle_layout(list(nodes))
    created = {}
    for name in nodes:
        rule = rule_for(name)
        tid = available.get(rule["template"], {}).get("template_id", "dry-template")
        x, y = pos[name]
        node = gns.add_node(pid, tid, name, x, y,args.compute_id)
        created[name] = node["node_id"]
        print(f"  node  {name:<14} -> {rule['template']}")

    print()
    for ((an, ai), (bn, bi)), ((_,aa,ap_),(_,ba,bp)) in zip(links,planned):
        gns.add_link(pid,
                     {"node_id": created[an], "adapter_number": aa, "port_number": ap_},
                     {"node_id": created[bn], "adapter_number": ba, "port_number": bp})
        print(f"  link  {an}:{ai:<7} <-> {bn}:{bi}")

    print(f"\nDone. Open the project '{args.project or lab_name}' in GNS3.")
    print("Startup configurations are NOT pushed: GNS3 appliances differ too much.")
    print("Review and translate configurations for the actual target NOS before applying them.")


if __name__ == "__main__":
    main()
