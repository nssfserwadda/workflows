from django import template

register = template.Library()

@register.filter
def div(value, arg):
    try:
        return value / arg
    except (ZeroDivisionError, TypeError):
        return None
