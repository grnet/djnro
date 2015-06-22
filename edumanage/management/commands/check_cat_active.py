# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

from django.core.management.base import BaseCommand
from django.conf import settings
from utils.cat_helper import CatQuery
from edumanage.models import CatEnrollment


class Command(BaseCommand):
    args = ''
    help = 'Checks if CAT enrollments have active registered IdP admins'

    def handle(self, *args, **options):
        all_cat_entries = CatEnrollment.objects.all()
        for catentry in all_cat_entries:
            instance = catentry.cat_instance
            cat_instance = settings.CAT_AUTH[instance]
            cat_api_key = cat_instance['CAT_API_KEY']
            cat_api_url = cat_instance['CAT_API_URL']
            inst_uid = catentry.cat_inst_id
            params = {"INST_IDENTIFIER": inst_uid}
            c = CatQuery(cat_api_key, cat_api_url)
            cq = c.admincount(params)
            if cq:
                if c.response['number_of_admins'] > 0:
                    if catentry.url != "ACTIVE":
                        catentry.url = "ACTIVE"
                        catentry.save()
