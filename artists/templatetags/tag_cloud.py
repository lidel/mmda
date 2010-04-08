from django import template
from django.template.loader import render_to_string

register = template.Library()

class TagCloudNode(template.Node):
    """
    Node that displays Cached*.tags
    """
    def __init__(self, tags):
        self.tags = template.Variable(tags)
    def render(self, context):
        try:
            actual_tags   = self.tags.resolve(context)
            return render_to_string('artists/tags/tags.html', {'tags':actual_tags})
        except template.VariableDoesNotExist:
            return ''

@register.tag
def tag_cloud_for(parser, token):
    tags = token.split_contents()[1]
    return TagCloudNode(tags)

