from django import forms
from django.utils.translation import gettext as _
from django.core.validators import EmailValidator


class MultipleEmailsField(forms.Field):
    def clean(self, value):
        """
        Check that the field contains one or more semicolon-separated emails
        and normalizes the data to a list of the email strings.
        """
        if not value:
            raise forms.ValidationError(_('Enter at least one e-mail address. Multiple email addresses Should be separated with semicolon (;)'))
        emails = value.split(';')
        for email in emails:
            # Create our own instance with
            # * blank whitelist - no '@localhost' permitted
            # * custom error message (referring to the email address being verified in question)
            # A failed validation will raise a ValidationError - no need to check return value
            EmailValidator(allowlist=[],message= _('%s is not a valid e-mail address.') % email)(email)

        # Always return the cleaned data.
        return ';'.join(emails)
