# encoding=utf-8
# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
import sys
import locale
import codecs
# Printing unicode: WAS: https://wiki.python.org/moin/PrintFails
# But now rather follow:
#    https://docs.djangoproject.com/en/1.9/howto/custom-management-commands/#management-commands-and-locales
# I.e., set leave_locale_alone and let the system locale handle things.
# Django 1.8 now uses unicode by default - so all works well without modifying the codecs.

from optparse import make_option
from django.core.management.base import BaseCommand
from accounts.models import User
from django.utils.translation import get_language, to_locale, gettext as _
from utils.locale import setlocale, compat_strxfrm


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

    def handle(self, *args, **options):
        users = User.objects.all()
        if not options['maillist']:
            self.stdout.write(
                u'{},{},{}'.format(
                    _('Institution'),
                    _('Administrator'),
                    "email"
                )
                + "\n"
            )
        data = [
            (
                u.userprofile.institution.get_name(get_language()),
                u.first_name + " " + u.last_name,
                m
            ) for u in users if (
                u.registrationprofile
                and u.registrationprofile.activation_key == "ALREADY_ACTIVATED"
            ) for m in u.email.split(';')
        ]
        with setlocale((to_locale(get_language()), 'UTF-8'),
                       locale.LC_COLLATE):
            data.sort(key=lambda d: compat_strxfrm(d[0]))
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
