"""Constructed two-stage hash-correlation model; not Linux or ASIC forwarding."""
import hashlib,json,collections
def bucket(flow,seed):return hashlib.sha256((seed+':'+str(flow)).encode()).digest()[0]&1
def model(second_seed):
 counts=collections.Counter((bucket(p,'stage-a'),bucket(p,second_seed)) for p in range(20000,21024))
 return {f'{a}->{b}':counts[a,b] for a in range(2) for b in range(2)}
print(json.dumps({'scope':__doc__,'same_function_inputs_seed':model('stage-a'),'different_seed':model('stage-b')},indent=2))
