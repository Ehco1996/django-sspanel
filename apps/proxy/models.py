import base64
import json
from decimal import Decimal
from functools import cached_property
from urllib.parse import quote, urlencode

import pendulum
from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict

from apps import constants as c
from apps import utils
from apps.ext import cache
from apps.mixin import BaseLogModel, BaseModel, SequenceMixin
from apps.sspanel.models import User


class BaseNodeModel(BaseModel):
    name = models.CharField("名字", max_length=32)
    server = models.CharField("服务器地址", help_text="支持逗号分隔传多个地址", max_length=256)
    enable = models.BooleanField("是否开启", default=True, db_index=True)

    class Meta:
        abstract = True

    @property
    def multi_server_address(self):
        # TODO 单节点支持多入口
        return self.server.split(",")


class ProxyNode(BaseNodeModel, SequenceMixin):

    NODE_TYPE_SS = "ss"
    NODE_TYPE_VLESS = "vless"
    NODE_TYPE_TROJAN = "trojan"
    NODE_CHOICES = (
        (NODE_TYPE_SS, NODE_TYPE_SS),
        (NODE_TYPE_VLESS, NODE_TYPE_VLESS),
        (NODE_TYPE_TROJAN, NODE_TYPE_TROJAN),
    )

    node_type = models.CharField(
        "节点类型", default=NODE_TYPE_SS, choices=NODE_CHOICES, max_length=32
    )
    info = models.CharField("节点说明", max_length=1024, blank=True)
    level = models.PositiveIntegerField(default=0)
    country = models.CharField(
        "国家", default="CN", max_length=5, choices=c.COUNTRIES_CHOICES
    )
    used_traffic = models.BigIntegerField("已用流量", default=0)
    total_traffic = models.BigIntegerField("总流量", default=settings.GB)
    enlarge_scale = models.DecimalField(
        "倍率",
        default=Decimal("1.0"),
        decimal_places=1,
        max_digits=10,
    )
    enable_direct = models.BooleanField("允许直连", default=True)

    ehco_listen_host = models.CharField("隧道监听地址", max_length=64, blank=True, null=True)
    ehco_listen_port = models.CharField("隧道监听端口", max_length=64, blank=True, null=True)
    ehco_listen_type = models.CharField(
        "隧道监听类型", max_length=64, choices=c.LISTEN_TYPES, default=c.LISTEN_RAW
    )
    ehco_transport_type = models.CharField(
        "隧道传输类型", max_length=64, choices=c.TRANSPORT_TYPES, default=c.TRANSPORT_RAW
    )

    class Meta:
        verbose_name = "代理节点"
        verbose_name_plural = "代理节点"
        ordering = ("sequence",)

    def __str__(self) -> str:
        return f"{self.name}({self.node_type})"

    @classmethod
    @cache.cached()
    def get_by_id_with_cache(cls, id):
        return cls.objects.get(id=id)

    @classmethod
    def get_active_nodes(cls, level=None):
        query = cls.objects.filter(enable=True)
        if level is not None:
            query = query.filter(level__lte=level)
        return list(
            query.select_related("ss_config")
            .prefetch_related("relay_rules")
            .order_by("sequence")
        )

    @classmethod
    def calc_total_traffic(cls):
        aggs = cls.objects.all().aggregate(used_traffic=models.Sum("used_traffic"))
        used_traffic = aggs["used_traffic"] or 0
        return utils.traffic_format(used_traffic)

    def get_ss_node_config(self):
        configs = {"users": []}
        ss_config = self.ss_config
        for user in User.objects.filter(level__gte=self.level).values(
            "id",
            "ss_port",
            "ss_password",
            "total_traffic",
            "upload_traffic",
            "download_traffic",
        ):
            enable = self.enable and user["total_traffic"] > (
                user["download_traffic"] + user["upload_traffic"]
            )
            if ss_config.multi_user_port:
                # NOTE 单端口多用户
                port = ss_config.multi_user_port
            else:
                port = port = user["ss_port"]
            configs["users"].append(
                {
                    "user_id": user["id"],
                    "port": port,
                    "password": user["ss_password"],
                    "enable": enable,
                    "method": ss_config.method,
                }
            )
        return configs

    def get_proxy_configs(self):
        if self.node_type == self.NODE_TYPE_SS:
            return self.get_ss_node_config()
        return {}

    def get_ehco_server_config(self):
        return {
            "relay_configs": [
                {
                    "listen": f"{self.ehco_listen_host}:{self.ehco_listen_port}",
                    "listen_type": self.ehco_listen_type,
                    "transport_type": self.ehco_transport_type,
                    "tcp_remotes": [f"127.0.0.1:{self.ehco_relay_port}"],
                    "udp_remotes": [],
                }
            ]
        }

    def get_user_ss_port(self, user):
        if not self.ss_config.multi_user_port:
            return user.ss_port
        return self.ss_config.multi_user_port

    def get_user_node_link(self, user, relay_rule=None):
        if self.node_type != self.NODE_TYPE_SS:
            return ""
        if relay_rule:
            host = relay_rule.relay_host
            port = relay_rule.relay_port
            remark = relay_rule.remark
        else:
            host = self.multi_server_address[0]
            port = self.get_user_ss_port(user)
            remark = self.name
        code = f"{self.ss_config.method}:{user.ss_password}@{host}:{port}"
        b64_code = base64.urlsafe_b64encode(code.encode()).decode()
        return "ss://{}#{}".format(b64_code, quote(remark))

    def get_user_clash_config(self, user, relay_rule=None):
        config = {}
        if self.node_type == self.NODE_TYPE_SS:
            if relay_rule:
                host = relay_rule.relay_host
                port = relay_rule.relay_port
                remark = relay_rule.remark
            else:
                host = self.multi_server_address[0]
                port = self.get_user_ss_port(user)
                remark = self.name
            config = {
                "name": remark,
                "type": self.NODE_TYPE_SS,
                "server": host,
                "port": port,
                "cipher": self.ss_config.method,
                "password": user.ss_password,
                "udp": True,
            }
        return json.dumps(config, ensure_ascii=False)

    def to_dict_with_extra_info(self, user):
        data = model_to_dict(self)
        data.update(UserTrafficLog.get_latest_online_log_info(self))
        data["country"] = self.country.lower()
        data["ss_password"] = user.ss_password
        data["node_link"] = self.get_user_node_link(user)
        data["multi_server_address"] = self.multi_server_address

        # NOTE ss only section
        if self.node_type == self.NODE_TYPE_SS:
            data["ss_port"] = self.get_user_ss_port(user)
            data["method"] = self.ss_config.method

        if self.enable_relay:
            data["enable_relay"] = True
            data["relay_rules"] = [
                rule.to_dict_with_extra_info(user)
                for rule in self.relay_rules.filter(relay_node__enable=True)
            ]
        return data

    @property
    def human_total_traffic(self):
        return utils.traffic_format(self.total_traffic)

    @property
    def human_used_traffic(self):
        return utils.traffic_format(self.used_traffic)

    @property
    def overflow(self):
        return (self.used_traffic) > self.total_traffic

    @property
    def api_endpoint(self):
        if self.node_type == self.NODE_TYPE_SS:
            params = {"token": settings.TOKEN}
            return settings.HOST + f"/api/proxy_configs/{self.id}/?{urlencode(params)}"
        # TODO vless/trojan
        return ""

    @property
    def ehco_api_endpoint(self):
        params = {"token": settings.TOKEN}
        return settings.HOST + f"/api/ehco_server_config/{self.id}/?{urlencode(params)}"

    @property
    def ehco_relay_port(self):
        if self.node_type == self.NODE_TYPE_SS:
            return self.ss_config.multi_user_port
        # TODO 支持其他节点类型
        return None

    @cached_property
    def online_info(self):
        return UserTrafficLog.get_latest_online_log_info(self)

    @cached_property
    def enable_relay(self):
        return bool(self.relay_rules.filter(relay_node__enable=True).exists())

    @cached_property
    def enable_ehco_tunnel(self):
        return self.ehco_listen_host and self.ehco_listen_port


class SSConfig(models.Model):
    proxy_node = models.OneToOneField(
        to=ProxyNode,
        related_name="ss_config",
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="代理节点",
        verbose_name="代理节点",
    )
    method = models.CharField(
        "加密类型", default=settings.DEFAULT_METHOD, max_length=32, choices=c.METHOD_CHOICES
    )
    multi_user_port = models.IntegerField(
        "多用户端口", help_text="单端口多用户端口", null=True, blank=True
    )

    class Meta:
        verbose_name = "SS配置"
        verbose_name_plural = "SS配置"

    def __str__(self) -> str:
        return self.proxy_node.__str__() + "-配置"


class RelayNode(BaseNodeModel):

    CMCC = "移动"
    CUCC = "联通"
    CTCC = "电信"
    BGP = "BGP"
    ISP_TYPES = (
        (CMCC, "移动"),
        (CUCC, "联通"),
        (CTCC, "电信"),
        (BGP, "BGP"),
    )

    isp = models.CharField("ISP线路", max_length=64, choices=ISP_TYPES, default=BGP)
    remark = models.CharField("备注", max_length=64, default="")

    class Meta:
        verbose_name = "中转节点"
        verbose_name_plural = "中转节点"

    def __str__(self) -> str:
        if self.remark:
            return f"{self.name}-{self.remark}"
        return self.name

    @classmethod
    def get_ip_list(cls):
        return [node.server for node in cls.objects.filter(enable=True)]

    def get_relay_rules_configs(self):
        data = []
        for rule in self.relay_rules.select_related("proxy_node").all():
            node = rule.proxy_node
            tcp_remotes = []
            udp_remotes = []
            for server in node.multi_server_address:
                if node.enable_ehco_tunnel:
                    tcp_remote = f"{server}:{node.ehco_listen_port}"
                else:
                    # TODO other node type
                    tcp_remote = f"{server}:{node.ss_config.multi_user_port}"
                if rule.transport_type in c.WS_TRANSPORTS:
                    tcp_remote = "wss://" + tcp_remote
                udp_remotes.append(f"{server}:{node.ss_config.multi_user_port}")
                tcp_remotes.append(tcp_remote)
            data.append(
                {
                    "label": node.name,
                    "listen": f"0.0.0.0:{rule.relay_port}",
                    "listen_type": rule.listen_type,
                    "tcp_remotes": tcp_remotes,
                    "udp_remotes": udp_remotes,
                    "transport_type": rule.transport_type,
                }
            )
        return {"relay_configs": data}

    @property
    def api_endpoint(self):
        params = {"token": settings.TOKEN}
        return settings.HOST + f"/api/ehco_relay_config/{self.id}/?{urlencode(params)}"


class RelayRule(BaseModel):

    proxy_node = models.ForeignKey(
        ProxyNode,
        on_delete=models.CASCADE,
        verbose_name="代理节点",
        related_name="relay_rules",
    )
    relay_node = models.ForeignKey(
        RelayNode,
        on_delete=models.CASCADE,
        verbose_name="中转节点",
        related_name="relay_rules",
    )

    relay_port = models.CharField("中转端口", max_length=64, blank=False, null=False)
    listen_type = models.CharField(
        "监听类型", max_length=64, choices=c.LISTEN_TYPES, default=c.LISTEN_RAW
    )
    transport_type = models.CharField(
        "传输类型", max_length=64, choices=c.TRANSPORT_TYPES, default=c.TRANSPORT_RAW
    )

    class Meta:
        verbose_name = "中转规则"
        verbose_name_plural = "中转规则"

    def __str__(self) -> str:
        return self.remark

    def to_dict_with_extra_info(self, user):
        data = model_to_dict(self)
        data["relay_link"] = self.proxy_node.get_user_node_link(user, self)
        data["relay_host"] = self.relay_host
        data["remark"] = self.remark
        return data

    @property
    def relay_host(self):
        return self.relay_node.server

    @property
    def enable(self):
        return self.relay_node.enable and self.proxy_node.enable

    @property
    def remark(self):
        name = f"{self.relay_node.name}{self.relay_node.isp}-{self.proxy_node.name}"
        if self.proxy_node.enlarge_scale != Decimal(1.0):
            name += f"-{self.proxy_node.enlarge_scale}倍"
        return name


class UserTrafficLog(BaseLogModel):

    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, verbose_name="用户", null=True
    )
    proxy_node = models.ForeignKey(
        ProxyNode,
        on_delete=models.DO_NOTHING,
        verbose_name="代理节点",
    )
    upload_traffic = models.BigIntegerField("上传流量", default=0)
    download_traffic = models.BigIntegerField("下载流量", default=0)

    tcp_conn_cnt = models.IntegerField(default=0, verbose_name="tcp链接数")
    ip_list = models.JSONField(verbose_name="IP地址列表", default=list)

    class Meta:
        verbose_name = "用户流量记录"
        verbose_name_plural = "用户流量记录"
        ordering = ["-created_at"]
        index_together = ["user", "proxy_node", "created_at"]

    def __str__(self) -> str:
        return f"用户流量记录:{self.id}"

    @classmethod
    def get_user_online_device_count(cls, user, minutes=10):
        """获取最近一段时间内用户在线设备数量"""
        now = utils.get_current_datetime()
        ips = set()
        for log in cls.objects.filter(
            user=user, created_at__range=[now.add(minutes=minutes * -1), now]
        ).values("ip_list"):
            ips.update(log["ip_list"])
        return len(ips)

    @classmethod
    def get_all_node_online_user_count(cls):
        now = utils.get_current_datetime()
        return (
            cls.objects.filter(
                created_at__range=[now.subtract(seconds=c.NODE_TIME_OUT), now]
            )
            .values("user")
            .count()
        )

    @classmethod
    def get_latest_online_log_info(cls, proxy_node):
        data = {"online": False, "online_user_count": 0, "tcp_conn_cnt": 0}
        now = utils.get_current_datetime()
        query = cls.objects.filter(
            proxy_node=proxy_node,
            created_at__range=[now.subtract(seconds=c.NODE_TIME_OUT), now],
        )
        data["online"] = query.exists()
        if data["online"]:
            data["online_user_count"] = (
                query.filter(user__isnull=False).values("user").distinct().count()
            )
            data["tcp_conn_cnt"] = query.aggregate(cnt=models.Sum("tcp_conn_cnt"))[
                "cnt"
            ]
        return data

    @classmethod
    def calc_user_total_traffic(cls, proxy_node, user_id):
        logs = cls.objects.filter(user_id=user_id, proxy_node=proxy_node)
        aggs = logs.aggregate(
            u=models.Sum("upload_traffic"), d=models.Sum("download_traffic")
        )
        ut = aggs["u"] or 0
        dt = aggs["d"] or 0
        return utils.traffic_format(ut + dt)

    @classmethod
    @cache.cached(ttl=c.CACHE_TTL_MONTH)
    def _get_active_user_count_by_datetime(cls, dt: pendulum.DateTime):
        qs = (
            cls.objects.filter(created_at__range=[dt.start_of("day"), dt.end_of("day")])
            .values("user_id")
            .distinct()
        )
        return qs.count()

    @classmethod
    def get_active_user_count_by_datetime(cls, dt: pendulum.DateTime):
        """获取指定日期的活跃用户数量,只有今天的数据会hit db"""
        today = utils.get_current_datetime()
        if dt.date() == today.date():
            return cls._get_active_user_count_by_datetime.uncached(cls, dt)
        return cls._get_active_user_count_by_datetime(dt.start_of("day"))

    @classmethod
    @cache.cached(ttl=c.CACHE_TTL_MONTH)
    def _calc_traffic_by_datetime(cls, date, user_id=None, proxy_node_id=None):
        qs = cls.objects.filter(
            created_at__range=[date.start_of("day"), date.end_of("day")]
        )
        if user_id:
            qs = qs.filter(user_id=user_id)
        if proxy_node_id:
            qs = qs.filter(proxy_node_id=proxy_node_id)
        aggs = qs.aggregate(
            u=models.Sum("upload_traffic"), d=models.Sum("download_traffic")
        )
        ut = aggs["u"] or 0
        dt = aggs["d"] or 0
        return round((ut + dt) / settings.GB, 2)

    @classmethod
    def calc_traffic_by_datetime(
        cls, dt: pendulum.DateTime, user_id=None, proxy_node=None
    ):
        """获取指定日期指定用户的流量,只有今天的数据会hit db"""
        if dt.date() == utils.get_current_datetime().date():
            return cls._calc_traffic_by_datetime.uncached(
                cls,
                dt,
                user_id,
                proxy_node.id if proxy_node else None,
            )
        return cls._calc_traffic_by_datetime(
            dt.start_of("day"),
            user_id,
            proxy_node.id if proxy_node else None,
        )

    @property
    def total_traffic(self):
        return utils.traffic_format(self.download_traffic + self.upload_traffic)
