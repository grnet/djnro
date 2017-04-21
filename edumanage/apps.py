# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from django.apps import AppConfig

class EdumanageAppConfig(AppConfig):
    name = 'edumanage'

    def ready(self):
        import edumanage.signals
