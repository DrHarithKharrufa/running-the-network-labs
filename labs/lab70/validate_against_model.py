"""Strict local teaching schema; NOT a YANG parser or a device validation RPC."""
def validate(intent):
    if type(intent) is not dict: return ['intent: must be an object']
    errors=[]
    allowed={'name','enabled','mtu','mode','vlan'}
    for k in intent:
        if k not in allowed: errors.append(f'{k}: unknown field')
    if type(intent.get('name')) is not str or not intent['name'].strip():
        errors.append('name: required nonempty string')
    if 'enabled' in intent and type(intent['enabled']) is not bool:
        errors.append('enabled: must be boolean')
    mode=intent.get('mode')
    if type(mode) is not str or mode not in ('access','routed'):
        errors.append('mode: required access or routed')
    for k,lo,hi in [('mtu',68,9216),('vlan',1,4094)]:
        if k in intent and (type(intent[k]) is not int or not lo<=intent[k]<=hi):
            errors.append(f'{k}: integer {lo}..{hi}; booleans are not integers here')
    if mode=='access' and 'vlan' not in intent: errors.append('vlan: required for access mode')
    if mode=='routed' and 'vlan' in intent: errors.append('vlan: not allowed in routed mode')
    return errors

if __name__=='__main__':
    for x in [{'name':'Ethernet1','mode':'access','vlan':30},
              {'name':4,'enabled':'false'},
              {'name':'Ethernet1','mode':'routed','mtu':True}]:
        print(x, validate(x))
    print('Local constraints only. Obtain the exact advertised YANG modules, features and deviations,')
    print('then validate the full intended datastore and device/service behaviour separately.')
