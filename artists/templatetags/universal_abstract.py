from django import template
from django.template.loader import render_to_string

register = template.Library()

class UniversalAbstractNode(template.Node):
    """
    High-lever api that render abstract for CachedArtists and CachedReleases.
    """
    def __init__(self, entity):
        self.entity = template.Variable(entity)
    def render(self, context):
        try:
            actual_entity = self.entity.resolve(context)
            if 'abstract' in actual_entity:
                return render_to_string('artists/tags/abstract.html', { 'entity': actual_entity })
            else:
                raise Exception
        # if entity has no abstract of is not a proper variable: we render nothing
        except Exception:
            return ''

@register.tag
def abstract_for(parser, token):
    entity = token.split_contents()[1]
    return UniversalAbstractNode(entity)

