from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from edumanage.models import *
from accounts.models import *
from django.conf import settings

from django.contrib.contenttypes.generic import BaseGenericInlineFormSet

import ipaddr

import pprint
import re

FQDN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'
DN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'


class MonLocalAuthnParamForm(forms.ModelForm):
    
    class Meta:
        model = MonLocalAuthnParam

class InstRealmMonForm(forms.ModelForm):
    
    class Meta:
        model = InstRealmMon

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile

class InstDetailsForm(forms.ModelForm):

    class Meta:
        model = InstitutionDetails
    
    def clean_oper_name(self):
        oper_name = self.cleaned_data['oper_name']
        institution = self.cleaned_data['institution']
        if institution.ertype in [2,3]:
            if oper_name:
                match = re.match(DN_RE, oper_name)
                if not match:
                    raise forms.ValidationError('Invalid domain name format.')
                return self.cleaned_data["oper_name"]
            else:
                raise forms.ValidationError('This field is required.')

class InstServerForm(forms.ModelForm):

    class Meta:
        model = InstServer
    
    def clean_ertype(self):
        ertype = self.cleaned_data['ertype']
        institution = self.cleaned_data['instid']
        inst_type = institution.ertype
        type_list = [inst_type]
        if inst_type == 3:
            type_list = [1, 2, 3]
        if ertype:
            if ertype not in type_list:
                raise forms.ValidationError('Server type cannot be different than institution type (%s)' %dict(self.fields['ertype'].choices)[inst_type])
            return self.cleaned_data["ertype"]
        else:
            raise forms.ValidationError('This field is required.')
    
    def clean_port(self):
        port = self.cleaned_data['port']
        institution = self.cleaned_data['instid']
        if institution.ertype in [1,3]:
            if port:
                return self.cleaned_data["port"]
            else:
                raise forms.ValidationError(_('This field is required.'))
    
    def clean_acct_port(self):
        acct_port = self.cleaned_data['acct_port']
        institution = self.cleaned_data['instid']
        if institution.ertype in [1,3]:
            if acct_port:
                return self.cleaned_data["acct_port"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_timeout(self):
        timeout = self.cleaned_data['timeout']
        institution = self.cleaned_data['instid']
        if institution.ertype in [1,3]:
            if timeout:
                return self.cleaned_data["timeout"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_retry(self):
        retry = self.cleaned_data['retry']
        institution = self.cleaned_data['instid']
        if institution.ertype in [1,3]:
            if retry:
                return self.cleaned_data["retry"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    
    def clean_host(self):
        host = self.cleaned_data['host']
        if host:
            match = re.match(FQDN_RE, host)
            if not match:
                print "not match"
                try:
                    address = ipaddr.IPNetwork(host)
                except Exception:
                        error_text = _('Invalid network address/hostname format')
                        raise forms.ValidationError(error_text)
        else:
            raise forms.ValidationError(_('This field is required.'))
        return self.cleaned_data["host"]
    

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
            raise forms.ValidationError, _("Fill in at least one location name in English")
        if "en" not in langs:
            raise forms.ValidationError, _("Fill in at least one location name in English")


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
            raise forms.ValidationError, _("Fill in at least the info url")
        if "info" not in url_types:
            raise forms.ValidationError, _("Fill in at least the info url")


