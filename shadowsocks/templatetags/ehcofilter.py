from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value,arg):
    return value.as_widget(attrs={'class':arg})

@register.filter(name='mix_name')
def mix_name(value,arg):
    value = str(value)
    mix_name = value[0]+'***'+value[-1]
    return mix_name

