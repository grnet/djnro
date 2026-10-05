# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode


class AdminLoginRedirectMiddleware:
    """
    Sends unauthenticated requests to /admin/ to the /manage/login/ method
    picker instead of Django's stock admin login form, carrying the original
    /admin/... URL along as ?next=. Whichever login method staff pick there
    (Shibboleth, local password, social) already knows how to bounce back to
    that `next` URL on success, so this needs no Shibboleth-specific logic of
    its own and /admin/ never has to be protected by mod_shib at the
    webserver level.

    Opt-in via settings.ADMIN_LOGIN_REDIRECT_ENABLED (off by default).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.ADMIN_LOGIN_REDIRECT_ENABLED and
            request.path.startswith('/admin/') and
            not request.user.is_authenticated
        ):
            # Absolute, since MANAGE_LOGIN_URL may be on another host and a
            # bare path would resolve against that host after login.
            return redirect(
                '%s?%s' % (
                    settings.MANAGE_LOGIN_URL or reverse('manage_login_front'),
                    urlencode({
                        REDIRECT_FIELD_NAME: request.build_absolute_uri()
                    })
                )
            )
        return self.get_response(request)
