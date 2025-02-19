from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin
from django.conf import settings
from django.core import validators
from six import python_2_unicode_compatible
from django.utils.translation import gettext_lazy as _
from edumanage.models import Institution
import re


def patch_username_maxlen(field, maxlen=255):
    field.max_length = maxlen
    # try also updating the help_text
    try:
        help_text = field.help_text._proxy____args[0]
        if help_text != None:
            field.help_text = _(re.sub("[0-9]+(?= characters)",
                                       str(maxlen),
                                       help_text))
    except:
        pass
    for v in field.validators:
        if isinstance(v, validators.MaxLengthValidator):
            v.limit_value = maxlen

class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        db_table = 'auth_user';
        verbose_name = _('user')
        verbose_name_plural = _('users')
patch_username_maxlen(User._meta.get_field('username'))

@python_2_unicode_compatible
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    is_social_active = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ("overview", "Can see registered user and respective institutions"),
        )

    def __str__(self):
        return "%s:%s" % (self.user.username, self.institution)
