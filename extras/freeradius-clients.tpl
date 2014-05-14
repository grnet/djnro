## -*- coding: utf-8 -*-
<%!
import re
%>\
% for inst in insts:
% if inst['type'] in (2, 3) and 'clients' in inst:
#{{{${' ' + inst['id'] if 'id' in inst else ''}
% for client in inst['clients']:
client ${client} {
        secret          = ${hosts[client]['secret']}
<%
ipaddr = re.split(r'/(?=[0-9]{1,2}$)', hosts[client]['host'])
%>\
        ipaddr          = ${ipaddr[0]}
% if len(ipaddr) > 1:
        netmask         = ${ipaddr[1]}
% endif
        nastype         = other
% if 'id' in inst:
        grnetopname     = 1${inst['id']}
% endif
        eduroamspco     = GR
}
% endfor
#}}}
% endif
% endfor
