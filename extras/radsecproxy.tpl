## -*- coding: utf-8 -*-
<%!
import re
def percent_escape(text):
    return re.sub(r'%(?=[0-9A-Fa-f]{2})', r'%25', text)
def realm_regex(text):
    if text.find('*.') == 0:
        text = re.sub(r'\.', r'\\.', text)
        text = re.sub(r'\*(?=\\.)', r'.+', text)
        return '"/@%s$"' % text
    else:
        return text
def wildcard_realm_least_precedence(a, b):
    if a.find('*.') == 0 and b.find('*.') != 0:
        return -1
    elif b.find('*.') == 0 and a.find('*.') != 0:
        return 1
    else:
        return 0
%>\
% for inst in insts:
% if True in [c in inst for c in ['clients', 'realms']]:
#{{{${' ' + inst['id'] if 'id' in inst else ''}
% if inst['type'] in (2, 3) and 'clients' in inst:
% for client in inst['clients']:
rewrite rewrite-${client}-sp {
        include /etc/radsecproxy.conf.d/rewrite-default-sp.conf
% if 'id' in inst:
        addAttribute 126:1${inst['id']}
% endif
}
client ${client} {
        host ${clients[client]['host']}
        IPv4Only on
        type udp
        secret ${clients[client]['secret'] | percent_escape}
        fticksVISCOUNTRY GR
% if 'id' in inst:
        fticksVISINST 1${inst['id']}
% endif
        rewriteIn rewrite-${client}-sp
}
% endfor
% endif
% if inst['type'] in (1, 3) and 'realms' in inst:
<%doc>
The following one-liner does the equivalent of:

inst_servers = set()
for r in inst['realms']:
    if 'proxy_to' in inst['realms'][r]:
        inst_servers.update(inst['realms'][r]['proxy_to'])
for srv in inst_servers:
</%doc>\
% for srv in set([s for r in inst['realms'] for s in inst['realms'][r]['proxy_to'] if 'proxy_to' in inst['realms'][r]]):
rewrite rewrite-${srv}-idp {
        include /etc/radsecproxy.conf.d/rewrite-default-idp.conf
}
server ${srv}${'-acct' if servers[srv]['rad_pkt_type'] == 'acct' else ''} {
        host ${servers[srv]['host']}
        IPv4Only on
        type udp
        port ${servers[srv]['auth_port'] if servers[srv]['rad_pkt_type'] in ('auth', 'auth+acct') else servers[srv]['acct_port']}
        secret ${servers[srv]['secret'] | percent_escape}
% if servers[srv]['status_server'] and servers[srv]['rad_pkt_type'] in ('auth', 'auth+acct'):
        StatusServer on
% endif
        rewriteIn rewrite-${srv}-idp
}
% if servers[srv]['rad_pkt_type'] == 'auth+acct':
server ${srv}-acct {
        host ${servers[srv]['host']}
        IPv4Only on
        type udp
        port ${servers[srv]['acct_port']}
        secret ${servers[srv]['secret'] | percent_escape}
% if servers[srv]['status_server']:
        #StatusServer on
% endif
        rewriteIn rewrite-${srv}-idp
}
% endif
% endfor
% for realm in sorted([r for r in inst['realms'] if 'proxy_to' in inst['realms'][r]], cmp=wildcard_realm_least_precedence, reverse=True):
realm ${realm | realm_regex} {
% for srv in inst['realms'][realm]['proxy_to']:
% if servers[srv]['rad_pkt_type'] in ('auth', 'auth+acct'):
        server ${srv}
% endif
% if servers[srv]['rad_pkt_type'] in ('acct', 'auth+acct'):
        accountingserver ${srv}-acct
% endif
% endfor
}
% endfor
% endif
#}}}
% endif
% endfor
