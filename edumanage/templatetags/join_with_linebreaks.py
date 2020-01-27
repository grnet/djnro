from django.template import Library
from django.template.defaultfilters import linebreaksbr

register = Library()

@register.filter(needs_autoescape=True)
def join_with_linebreaks(value, autoescape=True):
    try:
        value = "\n".join(value)
    except:
        return value
    return linebreaksbr(value, autoescape)
