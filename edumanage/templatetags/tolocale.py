from django import template

register = template.Library()

@register.filter
def tolocale(objtrans, translang):
    try:
        return objtrans.get_name(lang=translang)
    except AttributeError:
        if isinstance(objtrans, dict):
            return objtrans.get(translang, '')
        else:
            return objtrans

register.simple_tag(tolocale)
register.assignment_tag(tolocale, name='tolocale_get')
