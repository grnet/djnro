from django import forms
from django.utils.translation import ugettext as _
from edumanage.models import (
    URL_i18n,
    MonLocalAuthnParam,
    InstRealmMon,
    InstitutionDetails,
    InstServer,
    Contact,
    InstRealm,
    ServiceLoc,
    Coordinates,
    ERTYPES,
    ERTYPE_ROLES,
)
from accounts.models import UserProfile
from edumanage.fields import MultipleEmailsField
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet

import ipaddress
import re

FQDN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'
DN_RE = r'(^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$)'

def get_model_field(model, field_name):
    fields = forms.models.fields_for_model(
        model,
        fields=[field_name]
    )
    return fields[field_name]

class ModelFormWithPropertyFields(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.property_fields = getattr(self, '_property_fields', {})
        instance = kwargs.get('instance', None)
        if instance:
            initial = kwargs.get('initial', {})
            initial.update({
                field_name: getattr(instance, field_name)
                for field_name in self.property_fields
            })
            kwargs['initial'] = initial
        super(ModelFormWithPropertyFields, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs): # pylint: disable=arguments-differ
        for field_name in self.property_fields:
            setattr(self.instance, field_name, self.cleaned_data[field_name])
        return super(ModelFormWithPropertyFields, self).save(*args, **kwargs)

class URL_i18nForm(forms.ModelForm):

    class Meta:
        model = URL_i18n
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        valid_urltypes = kwargs.pop('valid_urltypes', [])
        super(URL_i18nForm, self).__init__(*args, **kwargs)
        if not valid_urltypes:
            return
        if not isinstance(valid_urltypes, (tuple, list)):
            valid_urltypes = [valid_urltypes]
        urltype_field = self.fields['urltype']
        choices = urltype_field.choices
        if not choices:
            return
        new_choices = tuple(choice for choice in choices
                            if not choice[0] or choice[0] in valid_urltypes)
        urltype_field.choices = urltype_field.widget.choices = new_choices


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
        if institution.ertype in ERTYPE_ROLES.SP:
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
            # for Institution IdP+SP accept any InstServer ertype
            if inst_type == ERTYPES.IDPSP:
                type_list = ERTYPES
            if ertype not in type_list:
                raise forms.ValidationError('Server type cannot be different than institution type (%s)' %dict(self.fields['ertype'].choices)[inst_type])
        return self.cleaned_data["ertype"]

    def clean_auth_port(self):
        auth_port = self.cleaned_data['auth_port']
        if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in ERTYPE_ROLES.IDP:
            if auth_port:
                return self.cleaned_data["auth_port"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_acct_port(self):
        acct_port = self.cleaned_data['acct_port']
        if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in ERTYPE_ROLES.IDP:
            if acct_port:
                return self.cleaned_data["acct_port"]
            else:
                raise forms.ValidationError(_('This field is required.'))

    def clean_rad_pkt_type(self):
        rad_pkt_type = self.cleaned_data['rad_pkt_type']
        if not 'ertype' in self.cleaned_data:
                raise forms.ValidationError(_('The Type field is required to validate this field.'))
        ertype = self.cleaned_data['ertype']
        if ertype in ERTYPE_ROLES.IDP:
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
                        address = ipaddress.ip_address(host)
                    if addr_type == 'ipv4':
                        address = ipaddress.IPv4Address(host)
                    if addr_type == 'ipv6':
                        address = ipaddress.IPv6Address(host)
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
                if server.ertype not in ERTYPE_ROLES.IDP:
                    error_text = _('Only IdP and IdP/SP server types are allowed')
                    raise forms.ValidationError(error_text)
        else:
            raise forms.ValidationError(_('This field is required.'))
        return self.cleaned_data["proxyto"]


class ServiceLocForm(ModelFormWithPropertyFields):

    latitude = get_model_field(Coordinates, 'latitude')
    longitude = get_model_field(Coordinates, 'longitude')
    _property_fields = ['latitude', 'longitude']

    class Meta:
        model = ServiceLoc
        fields = '__all__'
        exclude = ('coordinates',) # pylint: disable=modelform-uses-exclude


class Generici18nFormSetFact(BaseGenericInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.obj_descr = kwargs.pop('obj_descr')
        super(Generici18nFormSetFact, self).__init__(*args, **kwargs)

    def clean(self):
        error_msg = _("Fill in at least one %(obj_descr) in English") % {
            'obj_descr': self.obj_descr
        }
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
            raise forms.ValidationError(error_msg)
        if "en" not in langs:
            raise forms.ValidationError(error_msg)


class UrlFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
        return


class UrlFormSetFactInst(BaseGenericInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        url_types = []
        empty_forms = True
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if form.cleaned_data:
                empty_forms = False
            url_types.append(form.cleaned_data.get('urltype', None))
        error_msg = _("Fill in at least the info url")
        if empty_forms:
            raise forms.ValidationError(error_msg)
        if "info" not in url_types:
            raise forms.ValidationError(error_msg)
