from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from edumanage.models import Institution
import re


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        db_table = 'auth_user';
        verbose_name = _('user')
        verbose_name_plural = _('users')

User._meta.get_field('username').max_length = 255
# try also updating the help_text
try:
    help_text = User._meta.get_field('username').help_text._proxy____args[0]
    if help_text != None:
	User._meta.get_field('username').help_text = _(re.sub("[0-9]+ characters", "255 characters", help_text))
except:
    pass

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    institution = models.ForeignKey(Institution)
    is_social_active = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ("overview", "Can see registered user and respective institutions"),
        )

    def __unicode__(self):
        return "%s:%s" % (self.user.username, self.institution)
