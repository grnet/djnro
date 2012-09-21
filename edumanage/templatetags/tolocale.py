from django import template
from edumanage.models import * 

register = template.Library()

@register.filter
def do_tolocale(parser, token):
    try:
        tag_name, objtrans, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    return CurrentLocaleNode(objtrans, format_string)


class CurrentLocaleNode(template.Node):
    def __init__(self, objtrans, format_string):
        self.format_string = template.Variable(format_string)
        self.objtrans = template.Variable(objtrans)
    def render(self, context):
        objtrans = self.objtrans.resolve(context)
        translang = self.format_string.resolve(context)
        return objtrans.get_name(lang=translang)

register.tag('tolocale', do_tolocale)