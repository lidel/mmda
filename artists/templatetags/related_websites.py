from django import template
from django.template.loader import render_to_string

register = template.Library()

class RelatedWebsitesNode(template.Node):
    """
    Node that displays Cached*.urls
    """
    def __init__(self, entity, mbid):
        self.entity = template.Variable(entity)
        self.mbid   = template.Variable(mbid)
    def render(self, context):
        try:
            actual_entity   = self.entity.resolve(context)
            actual_mbid     = self.mbid.resolve(context)
            template_locals = {'entity':actual_entity, 'entity_type':str(self.entity).title(), 'mbid':actual_mbid}
            return render_to_string('artists/tags/urls.html', template_locals)
        except template.VariableDoesNotExist:
            return ''

@register.tag
def urls_for(parser, token):
    try:
        tag_name, entity, mbid = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    return RelatedWebsitesNode(entity, mbid)
