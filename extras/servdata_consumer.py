#!/usr/bin/env python
# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

import sys, os
import re
import argparse
from yaml import load
try:
    from yaml import \
        CLoader as Loader
except ImportError:
    from yaml import Loader
import requests
from mako.template import Template
from mako.lookup import TemplateLookup

SETTINGS = {
    "template_directory" : "/srv/www/djnro/extras",
    "template_cc_dir"    : "/tmp",
    "templates"          : [ "freeradius-clients",
                             "freeradius-proxy",
                             "radsecproxy" ],
    "description"        :
"""This program reads "servdata" and produces
configuration for various software using the respective
templates."""
    }

def exit_with_error(msg = ""):
    sys.stderr.write(msg + "\n")
    sys.exit(1)

class ServerDataReader:
    def __init__(self, src):
        self.src = src
        if re.match(r"^https?://", self.src) is not None:
            try:
                resp = requests.get(src)
            except ConnectionError:
                exit_with_error("Connection failed for %s" % src)
            if resp.status_code > 304 or not resp.ok:
                exit_with_error("Fetch failed from %s" % src)
            self.rawdata = resp.text
        else:
            try:
                with open(src, "r") as f:
                    self.rawdata = f.read()
            except EnvironmentError:
                exit_with_error("Read from %s failed" % src)
        if not len(self.rawdata) > 0:
            exit_with_error("Read 0 length data, ignoring")

        self.data = load(self.rawdata)
        if not isinstance(self.data, dict) or \
                False in [i in self.data for i in ['clients',
                                                   'servers',
                                                   'institutions']
                          ]:
                exit_with_error("Read unexpected data")

    def get_data(self, category):
        if not category in self.data:
            exit_with_error("'%s' data not found" % category)
        return self.data[category]

class ServerDataWriter:
    def __init__(self, *args, **kwargs):
        self.tplccdir = kwargs['tplccdir'] if 'tplccdir' in kwargs else None
        self.tpldirs = kwargs['tpldirs'] if 'tpldirs' in kwargs else [os.curdir]
        if 'tpls' not in kwargs or not isinstance(kwargs['tpls'], dict):
            exit_with_error("Output templates not defined")

        tpls_dict = {a: kwargs['tpls'][a] if a in kwargs['tpls'] and \
                         isinstance(kwargs['tpls'][a], dict) else {} \
                         for a in ['files', 'parmap']}
        self.tpls = type(
            self.__class__.__name__ + \
                ".Templates",
            (object,),
            tpls_dict
            )
        tplookup_kwargs = {
            "directories":     self.tpldirs,
            "output_encoding": 'utf-8',
            "encoding_errors": 'replace',
            "strict_undefined": True
            }
        if self.tplccdir:
            tplookup_kwargs["module_directory"] = self.tplccdir

        self.tplookup = TemplateLookup(**tplookup_kwargs)

    def render_tpl(self, tpl):
        if tpl not in self.tpls.files:
            exit_with_error("Template file not specified for template %s" % tpl)
        elif not self.tplookup.has_template(self.tpls.files[tpl]):
            exit_with_error("Template file not found: %s" % self.tpls.files[tpl])
        t = self.tplookup.get_template(self.tpls.files[tpl])
        return t.render(**self.tpls.parmap[tpl])

def main():
    parser = argparse.ArgumentParser(
        description=SETTINGS["description"],
        )
    parser.add_argument('--input',
                        required=True,
                        help="""read servdata from this
file or http(s) URL"""
                        )
    parser.add_argument('--tpl-dir',
                        action='append',
                        help="""look for templates in this
directory (may be used more than once) [default: %s]"""
                        % SETTINGS["template_directory"]
                        )
    parser.add_argument('--tpl-cc',
                        help="""compile templates
(written by default to %(const)s)""",
                        nargs='?',
                        const=SETTINGS["template_cc_dir"])
    for t in SETTINGS["templates"]:
        parser.add_argument('--%s' % t,
                            metavar=t.replace("-", "_").upper(),
                            help="""generate %(dest)s output
(write to %(metavar)s or stdout)""",
                            nargs='?',
                            type=argparse.FileType('w'),
                            const=sys.stdout,
                            default=None)
    opts = parser.parse_args()

    sr = ServerDataReader(opts.input)

    tpls = { 'files':  {},
             'parmap': {} }
    for t in SETTINGS["templates"]:
        tpls['files'][t] = "%s.tpl" % t
        tpls['parmap'][t] = {
            "insts": sr.get_data('institutions'),
            "clients": sr.get_data('clients'),
            "servers": sr.get_data('servers')
            }

    if opts.tpl_dir is None:
        opts.tpl_dir = [SETTINGS["template_directory"]]

    sw_kwargs = { "tpls": tpls,
                 "tpldirs": opts.tpl_dir }
    if opts.tpl_cc:
        sw_kwargs.update({ "tplccdir": opts.tpl_cc })

    sw = ServerDataWriter(**sw_kwargs)

    for t in SETTINGS["templates"]:
        to = t.replace('-', '_')
        if getattr(opts, to, None) is not None:
            getattr(opts, to).write(sw.render_tpl(t))

if __name__ == "__main__":
    main()
