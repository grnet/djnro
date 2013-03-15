from django import forms
from django.core.validators import email_re

class MultipleEmailsField(forms.Field):
    def clean(self, value):
        """
        Check that the field contains one or more semicolon-separated emails
        and normalizes the data to a list of the email strings.
        """
        if not value:
            raise forms.ValidationError('Enter at least one e-mail address. Multiple email addresses Should be separated with semicolon (;)')
        emails = value.split(';')
        for email in emails:
            if not email_re.match(email):
                raise forms.ValidationError('%s is not a valid e-mail address.' % email)

        # Always return the cleaned data.
        return ';'.join(emails)