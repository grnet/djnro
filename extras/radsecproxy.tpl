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
def wildcard_realm_least_precedence(key):
    return '~' + key \
        if (key.find('*.') == 0) else \
        key
def deduplicated_list(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]
%>\
<%
for inst in insts:
    if inst['type'] in ERTYPE_ROLES.SP and 'clients' in inst:
        for client in inst['clients']:
            if 'usecount' in clients[client]:
                clients[client]['usecount'] = clients[client]['usecount'] + 1
            else:
                clients[client]['usecount'] = 1
%>\
% for inst in insts:
% if True in [c in inst for c in ['clients', 'realms']]:
#{{{${' ' + inst['id'] if 'id' in inst else ''}
% if inst['type'] in ERTYPE_ROLES.SP and 'clients' in inst:
% for client in inst['clients']:
% if 'seen' in clients[client]:
# client ${client} defined previously
% else:
rewrite rewrite-${client}-sp {
        include /etc/radsecproxy.conf.d/rewrite-default-sp.conf
% if clients[client]['usecount'] == 1 and 'id' in inst:
        addAttribute 126:1${inst['id']}
% endif
}
client ${client} {
        host ${clients[client]['host']}
        IPv4Only on
        type udp
        secret ${clients[client]['secret'] | percent_escape}
        fticksVISCOUNTRY GR
% if clients[client]['usecount'] == 1 and 'id' in inst:
        fticksVISINST 1${inst['id']}
% endif
        rewriteIn rewrite-${client}-sp
}
% endif
<%
clients[client]['seen'] = True
%>\
% endfor
% endif
% if inst['type'] in ERTYPE_ROLES.IDP and 'realms' in inst:
<%doc>
The following one-liner does the equivalent of:

inst_servers = []
for r in inst['realms']:
    if 'proxy_to' in inst['realms'][r]:
        inst_servers.append(inst['realms'][r]['proxy_to'])
# deduplicate like set, but preserve order
inst_servers = deduplicated_list(inst_servers)
for srv in inst_servers:
</%doc>\
% for srv in deduplicated_list([s for r in inst['realms'] for s in inst['realms'][r]['proxy_to'] if 'proxy_to' in inst['realms'][r]]):
% if 'seen' in servers[srv]:
# server ${srv} defined previously
% else:
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
<%
servers[srv]['seen'] = True
%>\
% endif
% endfor
% for realm in sorted([r for r in inst['realms'] if 'proxy_to' in inst['realms'][r]], key=wildcard_realm_least_precedence):
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
