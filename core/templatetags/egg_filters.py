from django import template

register = template.Library()

@register.filter
def underscore(value):
    """Replaces spaces with underscores and lowercases the string."""
    return value.lower().replace(' ', '_')
