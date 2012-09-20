from django import template
from edumanage.models import * 

register = template.Library()

@register.filter
def do_tolocale(parser, token):
    print token
    try:
        tag_name, inst, format_string = token.split_contents()
        print inst
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    return CurrentLocaleNode(inst, format_string)


class CurrentLocaleNode(template.Node):
    def __init__(self, inst, format_string):
        self.format_string = format_string
        self.inst = template.Variable(inst)
        print self.format_string, "STING"
    def render(self, context):
        inst_pk = self.inst.resolve(context)
        return Institution.objects.get(pk=inst_pk).__unicode__(lang=str(self.format_string))

register.tag('tolocale', do_tolocale)