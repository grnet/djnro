# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

from optparse import make_option
from django.core.management.base import BaseCommand
from edumanage.models import InstServer, Institution


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--output',
            dest='output',
            default="yaml",
            help="Output type: json, yaml"
        ),
    )
    args = ''
    help = "Exports server data"

    def handle(self, *args, **options):
        if options['output'] == "yaml":
            from yaml import dump
            try:
                from yaml import CDumper as Dumper, CSafeDumper as SafeDumper
            except ImportError:
                from yaml import Dumper, SafeDumper
            self.stdout.write(
                dump(
                    servdata(),
                    Dumper=SafeDumper,
                    allow_unicode=True,
                    default_flow_style=False
                )
            )

        elif options['output'] == "json":
            from json import dumps

            self.stdout.write(
                dumps(
                    servdata(),
                    indent=2
                )
            )


def srv_identifier(srv, prefix):
    if not hasattr(srv, "id"):
        return None
    retid = "{0}{1:d}".format(prefix,
                              srv.id)
    if hasattr(srv, "name") and srv.name:
        from django.template.defaultfilters import slugify
        retid = "{0}_{1}".format(retid,
                                 slugify(srv.name))
    return retid


def servdata():
    root = {}
    hosts = InstServer.objects.all()
    insts = Institution.objects.all()

    clients = hosts.filter(ertype__in=[2,3])
    if clients:
        root['clients'] = {}
    for srv in clients:
        srv_id = srv_identifier(srv, "client_")
        srv_dict = {}
        srv_dict['host'] = srv.host
        if srv.name:
            srv_dict['label'] = srv.name
        srv_dict['secret'] = srv.secret
        root['clients'].update({srv_id: srv_dict})

    servers = hosts.filter(ertype__in=[1,3])
    if servers:
        root['servers'] = {}
    for srv in servers:
        srv_id = srv_identifier(srv, "server_")
        srv_dict = {}
        srv_dict['rad_pkt_type'] = srv.rad_pkt_type
        if srv.rad_pkt_type.find("auth") != -1:
            srv_dict['auth_port'] = srv.auth_port
        if srv.rad_pkt_type.find("acct") != -1:
            srv_dict['acct_port'] = srv.acct_port
        srv_dict['host'] = srv.host
        if srv.name:
            srv_dict['label'] = srv.name
        srv_dict['secret'] = srv.secret
        srv_dict['status_server'] = bool(srv.status_server)
        root['servers'].update({srv_id: srv_dict})

    if insts:
        root['institutions'] = []
    for inst in insts:
        inst_dict = {}
        if not hasattr(inst, "institutiondetails"):
            continue
        if hasattr(inst.institutiondetails, "oper_name") and \
                inst.institutiondetails.oper_name:
            inst_dict['id'] = inst.institutiondetails.oper_name
        inst_dict['type'] = inst.ertype
        if inst.ertype in (2, 3):
            inst_clients = inst.servers.filter(ertype__in=[2, 3])
            if inst_clients:
                inst_dict['clients'] = [srv_identifier(srv, "client_") for
                                        srv in inst_clients]
        if inst.ertype in (1, 3):
            inst_realms = inst.instrealm_set.all()
            if inst_realms:
                inst_dict['realms'] = {}
            for realm in inst_realms:
                rdict = {}
                rdict[realm.realm] = {}
                rdict[realm.realm]['proxy_to'] = [srv_identifier(proxy, "server_") for
                                                  proxy in realm.proxyto.all()]
                inst_dict['realms'].update(rdict)
        root['institutions'].append(inst_dict)

    return root
