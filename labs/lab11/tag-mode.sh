#!/usr/bin/env bash
# Run on the Containerlab host for this disposable topology only.
set -euo pipefail
case ${1:-} in
 experiment)
   docker exec clab-lab11-sw2 bridge vlan del dev eth2 vid 120
   docker exec clab-lab11-sw2 bridge vlan add dev eth2 vid 1 pvid untagged
   for sw in sw1 sw2; do
     docker exec "clab-lab11-$sw" bridge vlan add dev eth3 vid 1 pvid untagged
   done
   ;;
 restore)
   # Delete only experiment membership that actually exists; never hide an error.
   python3 - <<'PY'
import subprocess,json
for node,port,vid in [('sw1','eth3',1),('sw2','eth3',1),('sw2','eth2',1)]:
 base=['docker','exec','clab-lab11-'+node,'bridge']
 state=json.loads(subprocess.check_output([*base,'-j','vlan','show','dev',port]))
 if any(v.get('vlan')==vid for row in state for v in row.get('vlans',[])):
  subprocess.run([*base,'vlan','del','dev',port,'vid',str(vid)],check=True)
subprocess.run(['docker','exec','clab-lab11-sw2','bridge','vlan','add','dev','eth2','vid','120','pvid','untagged'],check=True)
PY
   ;;
 *) echo 'usage: tag-mode.sh experiment|restore' >&2; exit 2;;
esac
