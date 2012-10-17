from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from edumanage.models import *
from django.conf import settings

from django.contrib.contenttypes.generic import BaseGenericInlineFormSet


import pprint

class InstDetailsForm(forms.ModelForm):

    class Meta:
        model = InstitutionDetails      

class InstServerForm(forms.ModelForm):

    class Meta:
        model = InstServer

class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact

class InstRealmForm(forms.ModelForm):

    class Meta:
        model = InstRealm

class ServiceLocForm(forms.ModelForm):

    class Meta:
        model = ServiceLoc

class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact

class NameFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        langs = []
        emptyForms = True
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if len(form.cleaned_data) != 0:
                emptyForms = False
            langs.append(form.cleaned_data.get('lang', None))
        if emptyForms:        
            raise forms.ValidationError, "Fill in at least one location name in English"
        if "en" not in langs:
            raise forms.ValidationError, "Fill in at least one location name in English"


class UrlFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if len(form.cleaned_data) == 0:
                pass
        return
                
class UrlFormSetFactInst(BaseGenericInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        url_types = []
        emptyForms = True
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if len(form.cleaned_data) != 0:
                emptyForms = False
            url_types.append(form.cleaned_data.get('urltype',None))
        if emptyForms:        
            raise forms.ValidationError, "Fill in at least the info url"
        if "info" not in url_types:
            raise forms.ValidationError, "Fill in at least the info url"
