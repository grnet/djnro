from django.template.defaulttags import register

@register.filter
def dict_lookup(dictionary, key):
    return dictionary.get(key)
