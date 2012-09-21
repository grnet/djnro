from django import forms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from edumanage.models import *
from django.conf import settings



class InstDetailsForm(forms.ModelForm):

    class Meta:
        model = InstitutionDetails
        

class ServiceLocForm(forms.ModelForm):

    class Meta:
        model = ServiceLoc