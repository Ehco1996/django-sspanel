from django.contrib import admin
from . import models


class UserAdmin(admin.ModelAdmin):
        list_display=['username','balance',]
 
class InviteCodeAdmin(admin.ModelAdmin):
    list_display=['code','time_created']

class AliveipAdmin(admin.ModelAdmin):
    list_display=['user_name','ip_address','time']

class MoneyCodeAdmin(admin.ModelAdmin):
    list_display=['user','code','isused']
# Register your models here.
admin.site.register(models.User,UserAdmin)
admin.site.register(models.InviteCode,InviteCodeAdmin)
admin.site.register(models.Aliveip,AliveipAdmin)
admin.site.register(models.Node)
admin.site.register(models.Donate)
admin.site.register(models.MoneyCode,MoneyCodeAdmin)
admin.site.register(models.Shop)
