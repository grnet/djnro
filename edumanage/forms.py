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
            pprint.pprint(form.__dict__)
            if len(form.cleaned_data) != 0:
                emptyForms = False
            langs.append(form.cleaned_data.get('lang', None))
        if emptyForms:        
            raise forms.ValidationError, "Fill in at least one location name in English"
        if "en" not in langs:
            raise forms.ValidationError, "Fill in at least one location name in English"


class UrlFormSetFact(BaseGenericInlineFormSet):
    def clean(self):
        #raise forms.ValidationError, "Clean method called" 
        if any(self.errors):
            return
        pprint.pprint(self.forms)
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            
            pprint.pprint(len(form.cleaned_data))
            if len(form.cleaned_data) == 0:
                #raise forms.ValidationError, "Fill in at least one url "
                pass
                #print "ERROROROROR"
                #self.append_non_form_error("not enough subs")
             #   pass
        return
                
#        raise forms.ValidationError('Invalid date range')
         
    
#    def save(self, commit=True, request=None):
#        for uform in self.forms:
#            urls = uform.save(commit=False)
#            urls.content_object = self.instance
#            urls.save()
#        return self.save_existing_objects(commit) + self.save_new_objects(commit)


