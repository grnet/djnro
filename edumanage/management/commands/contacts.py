# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
import sys
import locale
import codecs
# sort greek utf-8 properly
locale.setlocale(locale.LC_COLLATE, ('el_GR', 'UTF8'))
# https://wiki.python.org/moin/PrintFails
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

from optparse import make_option
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--mail-list',
            action='store_true',
            dest='maillist',
            default=False,
            help='Return only emails (output suitable for a mailing list)'
        ),
    )
    args = ''
    help = 'Prints institution contacts in CSV format'

    def handle(self, *args, **options):
        users = User.objects.all()
        if not options['maillist']:
            self.stdout.write(
                u'"%s","%s","%s"' % (
                    u"Φορέας",
                    u"Διαχειριστής",
                    "email"
                )
                + "\n"
            )
        data = [
            (
                u.get_profile().institution.get_name('el'),
                u.first_name + " " + u.last_name,
                m
            ) for u in users if (
                u.registrationprofile
                and u.registrationprofile.activation_key == "ALREADY_ACTIVATED"
            ) for m in u.email.split(';')
        ]
        data.sort(key=lambda d: unicode(d[0]))
        for (foreas, onoma, email) in data:
            if options['maillist']:
                self.stdout.write(
                    u'{email}\t{onoma}'.format(
                        email=email,
                        onoma=onoma
                    )
                    + "\n")
            else:
                self.stdout.write(
                    u'"{foreas}","{onoma}","{email}"'.format(
                        onoma=onoma,
                        email=email,
                        foreas=foreas
                    )
                    + "\n"
                )
