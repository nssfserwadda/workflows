from django import template

register = template.Library()

@register.filter(name='user_in_group')
def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()



@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
