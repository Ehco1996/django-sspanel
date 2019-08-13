from django import template
from django.conf import settings

register = template.Library()


# 增加模板class
@register.filter(name="add_class")
def add_class(value, arg):
    return value.as_widget(attrs={"class": arg})


# 捐赠名混淆
@register.filter(name="mix_name")
def mix_name(value, arg):
    if value:
        value = str(value)
        mix_name = value[0] + "***" + value[-1]
    else:
        mix_name = "***"
    return mix_name


# 显示setting value
@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")
