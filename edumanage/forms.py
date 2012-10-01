from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from edumanage.models import *
from django.conf import settings

from django.contrib.contenttypes.generic import BaseGenericInlineFormSet


class InstDetailsForm(forms.ModelForm):

    class Meta:
        model = InstitutionDetails
        


class InstServerForm(forms.ModelForm):

    class Meta:
        model = InstServer

class ServiceLocForm(forms.ModelForm):

    class Meta:
        model = ServiceLoc


class NameFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
         super(NameFormSetFact, self).clean()
         print "SELLLL", self.forms
