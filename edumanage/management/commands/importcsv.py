# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

# Copyright © 2011-2014 Greek Research and Technology Network (GRNET S.A.)
#
# Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr),
# Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr) and Stavros Kroustouris
# (staurosk-at-noc-dot-grnet-dot-gr), GRNET NOC
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
'''
Django management command to import a CSV
'''

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from edumanage.models import InstRealmMon, MonLocalAuthnParam, InstRealm
import sys
import csv


class Command(BaseCommand):
    '''
    Django management command to import a CSV
    '''
    help = 'Loads a specific CSV to eduroam models'
    args = '<file>'
    label = 'file name to be imported'

    def handle(self, *args, **options):
        '''
        Handle command
        '''

        if args is None or len(args) != 1:
            raise CommandError('You must supply a file name')
        try:
            csvname = sys.argv[2]
        except IndexError:
            print(_('Error in usage. See help'))
            sys.exit(1)

        count = 0
        with open(csvname, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
                (
                    username,
                    password,
                    timeout,
                    port,
                    method,
                    eaptype,
                    eap2type
                ) = row[:7]

                realm = username.split('@')[1]
                try:
                    instrealm = InstRealm.objects.get(realm=realm)
                    instrealmmon = InstRealmMon(realm=instrealm, mon_type='localauthn')
                    instrealmmon.save()
                    monlocalauthnparams = MonLocalAuthnParam(
                        instrealmmonid=instrealmmon,
                        eap_method=eaptype,
                        phase2=eap2type,
                        username=username,
                        passwp=password
                    )
                    monlocalauthnparams.save()
                except InstRealm.DoesNotExist:
                    print("Realm %s does not exit" % realm)

                print('OK: realm %s' % (realm))
                count += 1
            print('Total ' + str(count))
