## -*- coding: utf-8 -*-
<%!
import re
def realm_disarm(text):
    return re.sub(r'\*\.', r'_wildcard_.', text)
def realm_regex(text):
    if text.find('*.') == 0:
        text = re.sub(r'\.', r'\\\\.', text)
        text = re.sub(r'\*(?=\\\\\.)', r'.+', text)
        return '"~%s$"' % text
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
% for inst in insts:
% if inst['type'] in (1, 3) and 'realms' in inst:
#{{{${' ' + inst['id'] if 'id' in inst else ''}
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
home_server ${srv} {
        type                 = ${servers[srv]['rad_pkt_type']}
        ipaddr               = ${servers[srv]['host']}
        port                 = ${servers[srv]['auth_port'] if servers[srv]['rad_pkt_type'] in ('auth', 'auth+acct') else servers[srv]['acct_port']}
        secret               = ${servers[srv]['secret']}
        response_window      = 20
        zombie_period        = 40
        revive_interval      = 120
        status_check         = ${'status-server' if servers[srv]['status_server'] else 'request'}
% if not servers[srv]['status_server']:
        username             = "eduroam-status_check"
        password             = "eduroam-status_check"
% endif
        check_interval       = 30
        num_answers_to_alive = 3
}
<%
servers[srv]['seen'] = True
%>\
% endif
% endfor
% for realm in sorted([r for r in inst['realms'] if 'proxy_to' in inst['realms'][r]], key=wildcard_realm_least_precedence):
<%
realm_servers = {}
for t in ['auth', 'acct', 'auth+acct']:
    realm_servers[t] = deduplicated_list([s for s in inst['realms'][realm]['proxy_to']
                                          if servers[s]['rad_pkt_type'] == t])
if len(realm_servers['auth+acct']) != len(inst['realms'][realm]['proxy_to']):
    realm_servers['auth'] += realm_servers['auth+acct']
    realm_servers['acct'] += realm_servers['auth+acct']
    realm_servers['auth+acct'] = []
%>\
% if len(realm_servers['auth+acct']) > 0:
home_server_pool ${realm | realm_disarm} {
        type = fail-over
% for srv in realm_servers['auth+acct']:
        home_server = ${srv}
% endfor
}
% else:
    % if len(realm_servers['auth']) > 0:
home_server_pool ${realm | realm_disarm}_auth {
        type = fail-over
        % for srv in realm_servers['auth']:
        home_server = ${srv}
        % endfor
}
    % endif
    % if len(realm_servers['acct']) > 0:
home_server_pool ${realm | realm_disarm}_acct {
        type = fail-over
        % for srv in realm_servers['acct']:
        home_server = ${srv}
        % endfor
}
    % endif
% endif
% if len(realm_servers['auth+acct']) > 0 or len(realm_servers['auth']) > 0:
realm ${realm | realm_regex} {
    % if len(realm_servers['auth+acct']) > 0:
        pool = ${realm | realm_disarm}
    % else:
        auth_pool = ${realm | realm_disarm}_auth
        % if len(realm_servers['acct']) > 0:
        acct_pool = ${realm | realm_disarm}_acct
        % else:
        acct_pool = reject_accounting
        % endif
    % endif
        nostrip
}
% endif
% endfor
#}}}
% endif
% endfor
