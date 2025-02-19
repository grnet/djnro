# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

import ldap

from django.contrib.auth.models import UserManager, Permission, Group
from accounts.models import User
from django.conf import settings
from  django.contrib.auth.backends import BaseBackend

class ldapBackend(BaseBackend):
    def authenticate(self, username=None, password=None):

        ldap_settings = settings.LDAP_AUTH_SETTINGS
        # Authenticate the base user so we can search
        # Go through servers using their corresponding DNs
        for ldap_setting in ldap_settings:
            uri = ldap_setting['url']
            base = ldap_setting['base']
            try:
                l = ldap.initialize(uri)
                l.start_tls_s()
            except ldap.LDAPError:
                continue
            else:
                l.protocol_version = ldap.VERSION3
                l.simple_bind_s()
                myUser = self._auth_user(base, username, password, l)
                if not myUser:
                    continue
                return myUser

    def _auth_user(self, base, username, password, l):

        scope = ldap.SCOPE_SUBTREE
        filter = "uid=" + username
        ret = ['dn', 'mail', 'givenName', 'sn']
        try:
            result_id = l.search(base, scope, filter, ret)
            result_type, result_data = l.result(result_id, 0)

            # If the user does not exist in LDAP, Fail.
            if (len(result_data) != 1):
                return None

            # We prevent a situation where binding could raise an exception with empty password
            # Plus security...
            if (len(password) == 0):
                return None
            # Attempt to bind to the user's DN
            l.simple_bind_s(result_data[0][0], password)

            # Checking to see if user has an e-mail
            try:
                mail = result_data[0][1]['mail'][0]
            except:
                mail = ''
            # The user existed and authenticated. Get the user record
            try:
                user = User.objects.get(username__exact=username)
                user.email = mail
                user.first_name = result_data[0][1]['givenName'][0]
                user.last_name = result_data[0][1]['sn'][0]
                user.is_active = True
                user.save()
            # The user did not exist. Create one with no privileges
            except:
                user = User.objects.create_user(username, mail, None)
                user.first_name = result_data[0][1]['givenName'][0]
                user.last_name = result_data[0][1]['sn'][0]
                user.is_staff = settings.LDAP_AUTH_IS_STAFF
                user.is_superuser = False
                user.is_active = True
                if settings.LDAP_AUTH_GROUP:
                    try:
                        g = Group.objects.get(name=settings.LDAP_AUTH_GROUP)
                        user.groups.add(g)
                        user.save()
                    except:
                        pass
            return user

        except ldap.INVALID_CREDENTIALS:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
