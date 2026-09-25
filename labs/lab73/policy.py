"""Bounded IOS XE policy-profile parser. Not a NOS syntax or reachability validator."""
import ipaddress
import re

PROFILE = "iosxe-vty-and-owned-interfaces-v1"

def check(config, owned_interfaces=("GigabitEthernet1/0/8","Loopback0")):
    if type(config) is not str or not config.strip():
        return {"profile":PROFILE,"status":"UNSUPPORTED","reason":"non-empty configuration required"}
    if not owned_interfaces or len(set(owned_interfaces))!=len(owned_interfaces):
        raise ValueError("explicit unique owned interfaces required")
    vty={};interfaces={};context=None;unsupported=[];violations=[];ended=False
    for number,line in enumerate(config.splitlines(),1):
        stripped=line.strip();lower=stripped.lower()
        if not stripped:continue
        if stripped.startswith('!'):context=None;continue
        if ended:unsupported.append(f'line {number}: content after end');continue
        if lower=='end':ended=True;context=None;continue
        if lower.startswith(('banner ','macro ','no line ','default line ','interface range ','no interface ','default interface ')):
            unsupported.append(f'line {number}: unsupported grammar');context=None;continue
        if not line[0].isspace():
            context=None
            if lower.startswith(('transport ','no transport ','default transport ')):
                unsupported.append(f'line {number}: transport command outside an indented VTY stanza');continue
            match=re.fullmatch(r'line vty (\d+)(?: (\d+))?',lower)
            if match:
                lo=int(match[1]);hi=int(match[2] or match[1])
                if not 0<=lo<=hi<=15:unsupported.append(f'line {number}: VTY range outside profile');continue
                context=('vty',list(range(lo,hi+1)))
                for i in context[1]:vty.setdefault(i,None)
            elif lower.startswith('line vty'):
                unsupported.append(f'line {number}: unsupported VTY header')
            elif lower.startswith('interface '):
                name=stripped.split(' ',1)[1]
                if ' ' in name:unsupported.append(f'line {number}: interface aliases/ranges unsupported');continue
                context=('interface',name);interfaces.setdefault(name,{'description':None,'ipv4':None})
            continue
        if context and context[0]=='vty':
            if lower.startswith('transport input '):
                tokens=lower.split()[2:]
                if len(tokens)!=len(set(tokens)) or not tokens or not set(tokens)<={'ssh','telnet','none','all'} or ('none' in tokens and len(tokens)>1) or ('all' in tokens and len(tokens)>1):
                    unsupported.append(f'line {number}: unsupported transport form')
                else:
                    for i in context[1]:vty[i]=set(tokens)
            elif lower.startswith(('no transport input','default transport input','transport ')):
                unsupported.append(f'line {number}: default/alternate transport outside profile')
        elif context and context[0]=='interface':
            record=interfaces[context[1]]
            if lower=='no description':record['description']=None
            elif lower.startswith('description '):record['description']=stripped.split(' ',1)[1].strip()
            elif lower.startswith('ip address '):
                parts=stripped.split()
                if len(parts)!=4:unsupported.append(f'line {number}: IPv4 address form outside profile')
                else:
                    try:record['ipv4']=ipaddress.IPv4Interface(f'{parts[2]}/{parts[3]}')
                    except ValueError:violations.append(f'line {number}: invalid IPv4 address/mask')
            elif lower.startswith(('no ip address','ip unnumbered','default ip address')):
                unsupported.append(f'line {number}: IPv4 deletion/default/unnumbered outside profile')
    for i in range(16):
        if i not in vty or vty[i] is None:unsupported.append(f'VTY {i}: explicit transport state absent')
        elif vty[i]&{'telnet','all'}:violations.append(f'VTY {i}: Telnet permitted by transport policy')
    for name in owned_interfaces:
        if name not in interfaces:unsupported.append(f'{name}: owned interface absent')
        elif not interfaces[name]['description']:violations.append(f'{name}: description absent')
    loopback=interfaces.get('Loopback0',{}).get('ipv4')
    if loopback is None:unsupported.append('Loopback0: explicit IPv4 state absent')
    elif loopback.ip not in ipaddress.IPv4Network('10.255.0.0/16') or loopback.network.prefixlen!=32:
        violations.append('Loopback0: organisation policy requires a /32 in 10.255.0.0/16')
    return {'profile':PROFILE,'status':'FAIL' if violations else 'UNSUPPORTED' if unsupported else 'PASS',
            'violations':violations,'unsupported':unsupported,
            'scope':'Only explicit VTY 0-15 transport, owned-interface descriptions and Loopback0 IPv4 allocation. No syntax, SSH usability, ACL, forwarding or service verdict.'}
