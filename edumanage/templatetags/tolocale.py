from django import template

register = template.Library()

@register.filter
def tolocale(objtrans, translang, get='name'):
    try:
        objtrans_method = getattr(objtrans, 'get_{}'.format(get))
        return objtrans_method(lang=translang)
    except AttributeError:
        if isinstance(objtrans, dict):
            return objtrans.get(translang, '')
        else:
            return objtrans

register.simple_tag(tolocale)
register.assignment_tag(tolocale, name='tolocale_get')
