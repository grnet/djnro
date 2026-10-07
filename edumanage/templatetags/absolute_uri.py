from django import template

register = template.Library()


@register.filter
def absolute_uri(request, path=''):
    """
    Return `path` as an absolute URL on the host that served `request`.
    Falls back to the current full path if `path` is empty.
    """
    return request.build_absolute_uri(path or request.get_full_path())
