## -*- coding: utf-8 -*-
<%!
import re
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
% if inst['type'] in ERTYPE_ROLES.SP and 'clients' in inst:
#{{{${' ' + inst['id'] if 'id' in inst else ''}
% for client in inst['clients']:
% if 'seen' in clients[client]:
# client ${client} defined previously
% else:
client ${client} {
        secret          = ${clients[client]['secret']}
<%
ipaddr = re.split(r'/(?=[0-9]{1,2}$)', clients[client]['host'])
%>\
        ipaddr          = ${ipaddr[0]}
% if len(ipaddr) > 1:
        netmask         = ${ipaddr[1]}
% endif
        nastype         = other
% if clients[client]['usecount'] == 1 and 'id' in inst:
        grnetopname     = 1${inst['id']}
% endif
        eduroamspco     = GR
}
<%
clients[client]['seen'] = True
%>\
% endif
% endfor
#}}}
% endif
% endfor
