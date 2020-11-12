from decimal import Decimal

from django.conf import settings
from django.db import models

from apps import constants as c
from apps.mixin import SequenceMixin


class ProxyNode(SequenceMixin):

    NODE_TYPE_SS = "ss"
    NODE_TYPE_VLESS = "vless"
    NODE_TYPE_TROJAN = "trojan"
    NODE_CHOICES = (
        (NODE_TYPE_SS, NODE_TYPE_SS),
        (NODE_TYPE_VLESS, NODE_TYPE_VLESS),
        (NODE_TYPE_TROJAN, NODE_TYPE_TROJAN),
    )

    name = models.CharField("名字", max_length=32)
    node_type = models.CharField(
        "节点类型", default=NODE_TYPE_SS, choices=NODE_CHOICES, max_length=32
    )
    server = models.CharField("服务器地址", help_text="支持逗号分隔传多个地址", max_length=256)
    info = models.CharField("节点说明", max_length=1024, blank=True)
    level = models.PositiveIntegerField(default=0)
    country = models.CharField(
        "国家", default="CN", max_length=5, choices=c.COUNTRIES_CHOICES
    )
    used_traffic = models.BigIntegerField("已用流量", default=0)
    total_traffic = models.BigIntegerField("总流量", default=settings.GB)
    enable = models.BooleanField("是否开启", default=True, db_index=True)
    enlarge_scale = models.DecimalField(
        "倍率", default=Decimal("1.0"), decimal_places=2, max_digits=10,
    )

    # for ss node
    method = None
    multi_user_port = None

    class Meta:
        verbose_name_plural = "代理节点"
        ordering = ("sequence",)


class SSConfig(models.Model):
    node = models.OneToOneField(
        to=ProxyNode,
        related_name="ss_config",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    method = models.CharField(
        "加密类型", default=settings.DEFAULT_METHOD, max_length=32, choices=c.METHOD_CHOICES
    )
    multi_user_port = models.IntegerField(
        "多用户端口", help_text="单端口多用户端口", null=True, blank=True
    )

    class Meta:
        verbose_name_plural = "SS节点配置"
