# encoding=utf-8
# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
import sys
import locale
import codecs
# sort greek utf-8 properly
locale.setlocale(locale.LC_COLLATE, ('el_GR', 'UTF-8'))
# Printing unicode: WAS: https://wiki.python.org/moin/PrintFails
# But now rather follow:
#    https://docs.djangoproject.com/en/1.9/howto/custom-management-commands/#management-commands-and-locales
# I.e., set leave_locale_alone and let the system locale handle things.
# Django 1.8 now uses unicode by default - so all works well without modifying the codecs.

from optparse import make_option
from django.core.management.base import BaseCommand
from django.utils import six
from accounts.models import User


class Command(BaseCommand):

    help = 'Prints institution contacts in CSV format'

    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--mail-list',
            action='store_true',
            dest='maillist',
            default=False,
            help='Return only emails (output suitable for a mailing list)'
        )

    def get_str_func(self):
        """Return a function suitable for conversion to string"""

        if six.PY3:
            return str
        else:
            return lambda s: unicode(s).encode('utf-8')

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
                u.userprofile.institution.get_name('el'),
                u.first_name + " " + u.last_name,
                m
            ) for u in users if (
                u.registrationprofile
                and u.registrationprofile.activation_key == "ALREADY_ACTIVATED"
            ) for m in u.email.split(';')
        ]
        data.sort(key=lambda d: locale.strxfrm(self.get_str_func()(d[0])))
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
