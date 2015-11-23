from django import template
from django.template.defaultfilters import stringfilter
from django.template.loader_tags import do_include
from django.template.defaulttags import CommentNode

register = template.Library()

@register.filter
@stringfilter
def template_exists(value):
    try:
        template.loader.get_template(value)
        return True
    except template.TemplateDoesNotExist:
        return False

@register.tag('include_maybe')
def do_include_maybe(parser, token):
    # Source: http://stackoverflow.com/a/18951166/15690
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            "%r tag takes at least one argument: "
            "the name of the template to be included." % bits[0])

    try:
        silent_node = do_include(parser, token)
    except template.TemplateDoesNotExist:
        # Django < 1.7
        return CommentNode()

    _orig_render = silent_node.render
    def wrapped_render(*args, **kwargs):
        try:
            return _orig_render(*args, **kwargs)
        except template.TemplateDoesNotExist:
            return CommentNode()
    silent_node.render = wrapped_render
    return silent_node
