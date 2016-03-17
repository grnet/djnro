from django import forms
from django.utils.translation import ugettext as _
from edumanage.models import (
    MonLocalAuthnParam,
    InstRealmMon,
    InstitutionDetails,
    InstServer,
    Contact,
    InstRealm,
    ServiceLoc
)
from accounts.models import UserProfile
from edumanage.fields import MultipleEmailsField
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet

import ipaddr
import re

FQDN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'
DN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'


class MonLocalAuthnParamForm(forms.ModelForm):

    class Meta:
        model = MonLocalAuthnParam
        fields = '__all__'


class InstRealmMonForm(forms.ModelForm):

    class Meta:
        model = InstRealmMon
        fields = '__all__'


class UserProfileForm(forms.ModelForm):

    email = MultipleEmailsField(required=True)

    class Meta:
        model = UserProfile
        fields = '__all__'


class InstDetailsForm(forms.ModelForm):

    class Meta:
        model = InstitutionDetails
        fields = '__all__'

    def clean_oper_name(self):
        oper_name = self.cleaned_data['oper_name']
        institution = self.cleaned_data['institution']
        if institution.ertype in [2, 3]:
            if oper_name:
                match = re.match(FQDN_RE, oper_name)
                if not match:
                    raise forms.ValidationError('Invalid domain name format.')
                return self.cleaned_data["oper_name"]
            else:
                raise forms.ValidationError('This field is required.')


class InstServerForm(forms.ModelForm):

    class Meta:
        model = InstServer
        fields = '__all__'
        exclude = ['instid']

    def clean_ertype(self):
        ertype = self.cleaned_data['ertype']
	if not ertype:
	    raise forms.ValidationError('This field is required.')
        for institution in self.inst_list:
	    inst_type = institution.ertype
	    type_list = [inst_type]
	    if inst_type == 3:
		type_list = [1, 2, 3]
		if ertype not in type_list:
		    raise forms.ValidationError('Server type cannot be different than institution type (%s)' %dict(self.fields['ertype'].choices)[inst_type])
	return self.cleaned_data["ertype"]

    def clean_auth_port(self):
        auth_port = self.cleaned_data['auth_port']
	if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in [1,3]:
            if auth_port:
                return self.cleaned_data["auth_port"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_acct_port(self):
        acct_port = self.cleaned_data['acct_port']
	if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in [1,3]:
            if acct_port:
                return self.cleaned_data["acct_port"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_rad_pkt_type(self):
        rad_pkt_type = self.cleaned_data['rad_pkt_type']
	if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in [1,3]:
            if rad_pkt_type:
                return self.cleaned_data["rad_pkt_type"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_host(self):
        host = self.cleaned_data['host']
        addr_type = self.cleaned_data['addr_type']
        if host:
            match = re.match(FQDN_RE, host)
            if not match:
                try:
                    if addr_type == 'any':
                        address = ipaddr.IPAddress(host)
                    if addr_type == 'ipv4':
                        address = ipaddr.IPv4Address(host)
                    if addr_type == 'ipv6':
                        address = ipaddr.IPv6Address(host)
                except Exception:
                        error_text = _('Invalid network address/hostname format')
                        raise forms.ValidationError(error_text)
        else:
            raise forms.ValidationError(_('This field is required.'))
        return self.cleaned_data["host"]


class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = '__all__'


class InstRealmForm(forms.ModelForm):

    class Meta:
        model = InstRealm
        fields = '__all__'

    def clean_proxyto(self):
        proxied_servers = self.cleaned_data['proxyto']
        if proxied_servers:
            for server in proxied_servers:
                if server.ertype not in [1,3]:
                    error_text = _('Only IdP and IdP/SP server types are allowed')
                    raise forms.ValidationError(error_text)
        else:
            raise forms.ValidationError(_('This field is required.'))
        return self.cleaned_data["proxyto"]


class ServiceLocForm(forms.ModelForm):

    class Meta:
        model = ServiceLoc
        fields = '__all__'


class NameFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        langs = []
        empty_forms = True
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if len(form.cleaned_data) != 0:
                empty_forms = False
            langs.append(form.cleaned_data.get('lang', None))
        if empty_forms:
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
        empty_forms = True
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if len(form.cleaned_data) != 0:
                empty_forms = False
            url_types.append(form.cleaned_data.get('urltype', None))
        if empty_forms:
            raise forms.ValidationError, _("Fill in at least the info url")
        if "info" not in url_types:
            raise forms.ValidationError, _("Fill in at least the info url")
