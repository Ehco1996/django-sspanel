import base64
import json
import random
from collections import defaultdict
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
from functools import cached_property
from urllib.parse import quote, urlencode

import pendulum
from django.conf import settings
from django.db import models, transaction
from django.db.models import F

from apps import constants as c
from apps import utils
from apps.ext import cache
from apps.mixin import BaseLogModel, BaseModel, SequenceMixin
from apps.sspanel.models import User


class XRayTags:
    APITag = "api"
    SSProxyTag = "ss_proxy"
    TrojanProxyTag = "trojan_proxy"
    SSRProxyTag = "ssr_proxy"
    VmessProxyTag = "vmess_proxy"
    VlessProxyTag = "vless_proxy"


class XRayTemplates:
    DEFAULT_CONFIG = {
        "stats": {},
        "api": {
            "tag": XRayTags.APITag,
            "services": ["StatsService", "HandlerService"],
        },
        "log": {"loglevel": "error"},
        "policy": {
            "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
            "system": {
                "statsInboundUplink": True,
                "statsInboundDownlink": True,
                "statsOutboundUplink": True,
                "statsOutboundDownlink": True,
            },
        },
        "inbounds": [
            {
                "listen": "127.0.0.1",
                "port": 23456,
                "protocol": "dokodemo-door",
                "settings": {"address": "127.0.0.1"},
                "tag": "api",
            },
        ],
        "outbounds": [{"tag": "direct", "protocol": "freedom", "settings": {}}],
        "routing": {
            "settings": {
                "rules": [
                    {
                        "type": "field",
                        "inboundTag": [XRayTags.APITag],
                        "outboundTag": XRayTags.APITag,
                    }
                ]
            }
        },
    }

    SS_INBOUND = {
        "listen": "0.0.0.0",
        "port": 0,
        "protocol": "shadowsocks",
        "tag": XRayTags.SSProxyTag,
        "settings": {"clients": [], "network": "tcp"},
    }

    SSR_INBOUND = {
        "listen": "192.168.0.0",
        "port": 0,
        "protocol": "shadowsocksr",
        "tag": XRayTags.SSRProxyTag,
        "settings": {"clients": [], "network": "tcp"},
    }

    TROJAN_INBOUND = {
        "listen": "0.0.0.0",
        "port": 0,
        "protocol": "trojan",
        "tag": XRayTags.TrojanProxyTag,
        "settings": {
            "clients": [],
            "network": "tcp",
            "fallbacks": [{"dest": ""}],
        },
        "streamSettings": {
            "network": "tcp",
            "security": "tls",
            "tlsSettings": {"alpn": ["http/1.1"]},
        },
    }

    VMESS_INBOUND = {
        "listen": "192.168.0.0",
        "port": 0,
        "protocol": "vmess",
        "tag": XRayTags.VmessProxyTag,
        "settings": {
            "clients": [],
            "network": "tcp",
            "fallbacks": [{"dest": ""}],
        },
        "streamSettings": {
            "network": "tcp",
            "security": "tls",
            "tlsSettings": {"alpn": ["http/1.1"]},
        },
    }

    VLESS_INBOUND = {
        "listen": "192.168.0.0",
        "port": 0,
        "protocol": "vless",
        "tag": XRayTags.VlessProxyTag,
        "settings": {
            "clients": [],
            "network": "tcp",
            "fallbacks": [{"dest": ""}],
        },
        "streamSettings": {
            "network": "tcp",
            "security": "tls",
            "tlsSettings": {"alpn": ["http/1.1"]},
        },
    }

    @classmethod
    def gen_base_config(cls, xray_grpc_port, log_level):
        xray_config = deepcopy(XRayTemplates.DEFAULT_CONFIG)
        xray_config["inbounds"][0]["port"] = xray_grpc_port
        xray_config["log"]["loglevel"] = log_level
        return xray_config


class BaseNodeModel(BaseModel):
    name = models.CharField("名字", max_length=32)
    server = models.CharField("服务器地址", help_text="服务器地址", max_length=256)
    enable = models.BooleanField("是否开启", default=True, db_index=True)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="成本", default=0
    )
    enlarge_scale = models.DecimalField(
        "倍率",
        default=Decimal("1.0"),
        decimal_places=1,
        max_digits=10,
    )

    class Meta:
        abstract = True

    @classmethod
    def calc_all_cost_price(cls):
        aggs = cls.objects.all().aggregate(cost_price=models.Sum("cost_price"))
        return aggs["cost_price"] or 0


class ProxyNode(BaseNodeModel, SequenceMixin):
    NODE_TYPE_SS = "ss"
    NODE_TYPE_TROJAN = "trojan"
    NODE_TYPE_SSR = "ssr"
    NODE_TYPE_VMESS = "vmess"
    NODE_TYPE_VLESS = "vless"
    NODE_TYPE_SET = {
        NODE_TYPE_SS,
        NODE_TYPE_TROJAN,
        NODE_TYPE_SSR,
        NODE_TYPE_VMESS,
        NODE_TYPE_VLESS,
    }
    NODE_CHOICES = (
        (NODE_TYPE_SS, NODE_TYPE_SS),
        (NODE_TYPE_TROJAN, NODE_TYPE_TROJAN),
        (NODE_TYPE_SSR, NODE_TYPE_SSR),
        (NODE_TYPE_VMESS, NODE_TYPE_VMESS),
        (NODE_TYPE_VLESS, NODE_TYPE_VLESS),
    )

    EHCO_LOG_LEVELS = (
        ("debug", "debug"),
        ("info", "info"),
        ("warn", "warn"),
        ("error", "error"),
    )

    node_type = models.CharField(
        "节点类型", default=NODE_TYPE_SS, choices=NODE_CHOICES, max_length=32
    )
    info = models.CharField("节点说明", max_length=1024, blank=True)
    level = models.PositiveIntegerField(default=0)
    country = models.CharField(
        "国家", default="CN", max_length=5, choices=c.COUNTRIES_CHOICES
    )
    used_traffic = models.BigIntegerField("已用流量(单位字节)", default=0)
    total_traffic = models.BigIntegerField("总流量(单位字节)", default=settings.GB)
    enable_direct = models.BooleanField("允许直连", default=True)
    enable_udp = models.BooleanField("是否开启UDP 转发", default=True)
    xray_grpc_port = models.IntegerField("xray grpc port", default=23456)
    provider_remark = models.CharField("vps备注", max_length=64, default="")

    ehco_listen_host = models.CharField("隧道监听地址", max_length=64, blank=True, null=True)
    ehco_listen_port = models.CharField("隧道监听端口", max_length=64, blank=True, null=True)
    ehco_listen_type = models.CharField(
        "隧道监听类型", max_length=64, choices=c.LISTEN_TYPES, default=c.LISTEN_RAW
    )
    ehco_transport_type = models.CharField(
        "隧道传输类型", max_length=64, choices=c.TRANSPORT_TYPES, default=c.TRANSPORT_RAW
    )
    ehco_web_port = models.IntegerField("隧道web端口", default=0)
    ehco_web_token = models.CharField(
        "隧道web token", max_length=64, blank=True, null=True
    )
    ehco_log_level = models.CharField(
        "隧道日志等级", max_length=64, default="info", choices=EHCO_LOG_LEVELS
    )
    ehco_reload_interval = models.IntegerField("配置重载间隔", default=0)

    upload_bandwidth_bytes = models.BigIntegerField("上传带宽", default=0)
    current_used_upload_bandwidth_bytes = models.BigIntegerField("当前使用的上传带宽", default=0)
    download_bandwidth_bytes = models.BigIntegerField("下载带宽", default=0)
    current_used_download_bandwidth_bytes = models.BigIntegerField(
        "当前使用的下载带宽", default=0
    )

    class Meta:
        verbose_name = "代理节点"
        verbose_name_plural = "代理节点"
        ordering = ("sequence",)

    def __str__(self) -> str:
        return f"{self.name}-{self.node_type}-{self.id}"

    @classmethod
    @cache.cached()
    def get_by_id_with_cache(cls, id):
        return cls.objects.get(id=id)

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.filter(id=id).first()

    @classmethod
    def get_active_nodes(cls):
        query = cls.objects.filter(enable=True)
        return (
            query.select_related("ss_config", "trojan_config")
            .prefetch_related("relay_rules")
            .order_by("sequence")
        )

    @classmethod
    def get_user_active_nodes(cls, user):
        # 1. filter by user level
        base_query = cls.get_active_nodes()
        query = base_query.filter(level__lte=user.level)
        # 2. filter out nodes that has been occupied by other users
        occupied_node_ids = [
            i["proxy_node_id"] for i in UserProxyNodeOccupancy.get_occupied_node_ids()
        ]
        not_occupied_node_ids = [
            i["id"] for i in query.exclude(id__in=occupied_node_ids).values("id")
        ]
        # 3. add nodes that has been occupied by this user
        user_occupied_node_ids = [
            i["proxy_node_id"]
            for i in UserProxyNodeOccupancy.get_user_occupied_node_ids(user)
        ]
        return cls.objects.filter(id__in=not_occupied_node_ids) | cls.objects.filter(
            id__in=user_occupied_node_ids
        )

    @classmethod
    def calc_total_traffic(cls):
        aggs = cls.objects.all().aggregate(used_traffic=models.Sum("used_traffic"))
        used_traffic = aggs["used_traffic"] or 0
        return utils.traffic_format(used_traffic)

    @classmethod
    def get_by_ip(clc, ip: str):
        return clc.objects.filter(server=ip).first()

    def get_node_users(self):
        # 1. if node is not enable, return empty list
        if not self.enable:
            return []
        # 2. node occupied by users, return users
        occupancies_query = UserProxyNodeOccupancy.get_node_occupancies(self)
        if occupancies_query.count() > 0:
            user_ids = occupancies_query.values("user_id")
            return User.objects.filter(id__in=user_ids)
        # 3. shared node filter user that level >= node.level
        return User.objects.filter(level__gte=self.level)

    def get_proxy_configs(self):
        if self.node_type == self.NODE_TYPE_SS:
            proxy_cfg = self.ss_config
        elif self.node_type == self.NODE_TYPE_TROJAN:
            proxy_cfg = self.trojan_config
        else:
            raise Exception("not support node type")

        configs = proxy_cfg.to_node_config(self)
        configs["users"] = [
            proxy_cfg.to_user_config(self, user) for user in self.get_node_users()
        ]
        return configs

    def get_ehco_server_config(self):
        if self.enable_ehco_tunnel:
            return {
                "web_port": self.ehco_web_port,
                "web_token": self.ehco_web_token,
                "log_level": self.ehco_log_level,
                "reload_interval": self.ehco_reload_interval,
                "relay_configs": [
                    {
                        "listen": f"{self.ehco_listen_host}:{self.ehco_listen_port}",
                        "listen_type": self.ehco_listen_type,
                        "transport_type": self.ehco_transport_type,
                        "tcp_remotes": [f"127.0.0.1:{self.ehco_relay_port}"],
                        "udp_remotes": [],
                    }
                ],
            }
        return {}

    def get_user_port(self):
        if self.node_type == self.NODE_TYPE_SS:
            return self.ss_config.multi_user_port
        elif self.node_type == self.NODE_TYPE_TROJAN:
            return self.trojan_config.multi_user_port

    def get_user_shadowrocket_sub_link(self, user, relay_rule=None):
        if relay_rule:
            host = relay_rule.relay_host
            port = relay_rule.relay_port
            remark = relay_rule.remark
            udp = relay_rule.enable_udp and self.enable_udp
        else:
            host = self.server
            port = self.get_user_port()
            remark = self.remark
            udp = self.enable_udp
        if self.node_type == self.NODE_TYPE_SS:
            code = f"{self.ss_config.method}:{user.proxy_password}@{host}:{port}"
            b64_code = base64.urlsafe_b64encode(code.encode()).decode()
        elif self.node_type == self.NODE_TYPE_TROJAN:
            code = f"{user.proxy_password}@{host}:{port}?allowInsecure=1&udp={udp}"
            b64_code = code  # trojan don't need base64 encode
        return f"{self.node_type}://{b64_code}#{quote(remark)}"

    def get_user_clash_config(self, user, relay_rule=None):
        if relay_rule:
            host = relay_rule.relay_host
            port = relay_rule.relay_port
            remark = relay_rule.remark
            udp = relay_rule.enable_udp and self.enable_udp
        else:
            host = self.server
            remark = self.remark
            udp = self.enable_udp
            port = self.get_user_port()

        config = {
            "name": remark,
            "type": self.node_type,
            "server": host,
            "password": user.proxy_password,
            "udp": udp,
            "port": port,
        }
        if self.node_type == self.NODE_TYPE_SS:
            config["cipher"] = self.ss_config.method
        if self.node_type == self.NODE_TYPE_TROJAN:
            config["skip-cert-verify"] = True

        return json.dumps(config, ensure_ascii=False)

    def get_enabled_relay_rules(self):
        return self.relay_rules.filter(relay_node__enable=True)

    def get_inbound_listen_host(self):
        if self.enable_direct:
            return "0.0.0.0"
        # if self.enable_relay , we need check if there is a raw transport relay rule
        if self.enable_relay:
            for rule in self.get_enabled_relay_rules():
                if rule.transport_type == c.TRANSPORT_RAW:
                    return "0.0.0.0"
        return "127.0.0.1"

    def reset_random_multi_user_port(self):
        if self.node_type == self.NODE_TYPE_SS:
            return self.ss_config.reset_random_multi_user_port()
        elif self.node_type == self.NODE_TYPE_TROJAN:
            return self.trojan_config.reset_random_multi_user_port()

    @property
    def human_total_traffic(self):
        return utils.traffic_format(self.total_traffic)

    @property
    def human_used_traffic(self):
        return utils.traffic_format(self.used_traffic)

    @property
    def human_used_current_traffic_rate(self):
        upload_rate = utils.traffic_rate_format(
            self.current_used_upload_bandwidth_bytes
        )
        download_rate = utils.traffic_rate_format(
            self.current_used_download_bandwidth_bytes
        )
        return f"up:{upload_rate} - down:{download_rate}"

    @property
    def overflow(self):
        return (self.used_traffic) > self.total_traffic

    @property
    def api_endpoint(self):
        params = {"token": settings.TOKEN}
        return f"{settings.SITE_HOST}/api/proxy_configs/{self.id}/?{urlencode(params)}"

    @property
    def ehco_relay_port(self):
        if self.node_type == self.NODE_TYPE_SS:
            return self.ss_config.multi_user_port
        elif self.node_type == self.NODE_TYPE_TROJAN:
            return self.trojan_config.multi_user_port
        return None

    @property
    def relay_count(self):
        return self.relay_rules.all().count()

    @cached_property
    def online_info(self):
        return UserTrafficLog.get_latest_online_log_info(self)

    @cached_property
    def enable_relay(self):
        return self.get_enabled_relay_rules().exists()

    @cached_property
    def enable_ehco_tunnel(self):
        return self.ehco_listen_host and self.ehco_listen_port

    @cached_property
    def remark(self):
        name = self.name
        if self.enlarge_scale != Decimal(1.0):
            name = f"[{self.enlarge_scale}x]{name}"
        return name

    @transaction.atomic
    def duplicate(self):
        new_node = deepcopy(self)
        new_node.id = None
        new_node.name = f"{new_node.name}-副本"
        new_node.enable = False
        new_node.save()
        if self.node_type == self.NODE_TYPE_SS:
            new_node.ss_config = deepcopy(self.ss_config)
            new_node.ss_config.id = None
            new_node.ss_config.proxy_node = new_node
            new_node.ss_config.save()
        elif self.node_type == self.NODE_TYPE_TROJAN:
            new_node.trojan_config = deepcopy(self.trojan_config)
            new_node.trojan_config.id = None
            new_node.trojan_config.proxy_node = new_node
            new_node.trojan_config.save()

        occupancy_config = OccupancyConfig.objects.filter(proxy_node=self).first()
        if occupancy_config:
            new_occupancy_config = deepcopy(occupancy_config)
            new_occupancy_config.id = None
            new_occupancy_config.proxy_node = new_node
            new_occupancy_config.save()
        return new_node


class resetPortMixin:
    def reset_random_multi_user_port(self):
        self.multi_user_port = random.randint(10024, 65535)
        self.save()
        return self.multi_user_port


class SSConfig(models.Model, resetPortMixin):
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
        return f"{self.proxy_node.__str__()}-配置"

    def to_node_config(self, node: ProxyNode):
        xray_config = XRayTemplates.gen_base_config(
            node.xray_grpc_port,
            node.ehco_log_level,
        )
        ss_config = self
        ss_inbound = deepcopy(XRayTemplates.SS_INBOUND)
        ss_inbound["listen"] = node.get_inbound_listen_host()
        ss_inbound["port"] = ss_config.multi_user_port
        if node.enable_udp:
            ss_inbound["settings"]["network"] += ",udp"
        xray_config["inbounds"].append(ss_inbound)
        configs = {
            "xray_config": xray_config,
            "sync_traffic_endpoint": node.api_endpoint,
        }
        configs.update(node.get_ehco_server_config())
        return configs

    def to_user_config(self, node: ProxyNode, user: User):
        enable = node.enable and user.total_traffic > (
            user.download_traffic + user.upload_traffic
        )
        return {
            "user_id": user.id,
            "password": user.proxy_password,
            "enable": enable,
            "method": self.method,
            "protocol": ProxyNode.NODE_TYPE_SS,
        }


class TrojanConfig(models.Model, resetPortMixin):
    proxy_node = models.OneToOneField(
        to=ProxyNode,
        related_name="trojan_config",
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="代理节点",
        verbose_name="代理节点",
    )
    fallback_addr = models.CharField("回落端口", default="", max_length=32)
    multi_user_port = models.IntegerField(
        "多用户端口", help_text="单端口多用户端口", null=True, blank=True
    )

    class Meta:
        verbose_name = "SS配置"
        verbose_name_plural = "SS配置"

    def __str__(self) -> str:
        return f"{self.proxy_node.__str__()}-配置"

    def to_node_config(self, node: ProxyNode):
        xray_config = XRayTemplates.gen_base_config(
            node.xray_grpc_port,
            node.ehco_log_level,
        )
        inbound = deepcopy(XRayTemplates.TROJAN_INBOUND)
        inbound["listen"] = node.get_inbound_listen_host()
        inbound["port"] = self.multi_user_port
        inbound["settings"]["fallbacks"][0]["dest"] = self.fallback_addr
        if node.enable_udp:
            inbound["settings"]["network"] += ",udp"
        xray_config["inbounds"].append(inbound)
        configs = {
            "users": [],
            "xray_config": xray_config,
            "sync_traffic_endpoint": node.api_endpoint,
        }
        configs.update(node.get_ehco_server_config())
        return configs

    def to_user_config(self, node: ProxyNode, user: User):
        enable = node.enable and user.total_traffic > (
            user.download_traffic + user.upload_traffic
        )
        return {
            "user_id": user.id,
            "password": user.proxy_password,
            "enable": enable,
            "protocol": ProxyNode.NODE_TYPE_TROJAN,
        }


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
    enable_ping = models.BooleanField("是否开启PING", default=True)
    enable_udp = models.BooleanField("是否开启UDP 转发", default=True)
    web_port = models.IntegerField("Web端口", default=0)
    web_token = models.CharField(
        "Web验证Token", max_length=64, default="", null=True, blank=True
    )

    class Meta:
        verbose_name = "中转节点"
        verbose_name_plural = "中转节点"

    def __str__(self) -> str:
        return f"{self.name}-{self.remark}" if self.remark else self.name

    def get_relay_rules_configs(self):
        data = []
        for rule in self.relay_rules.select_related("proxy_node").all():
            node: ProxyNode = rule.proxy_node
            if not node.enable:
                continue
            tcp_remotes = []
            udp_remotes = []
            if node.enable_ehco_tunnel and rule.transport_type != c.TRANSPORT_RAW:
                tcp_remote = f"{node.server}:{node.ehco_listen_port}"
            else:
                tcp_remote = f"{node.server}:{node.get_user_port()}"
            if rule.transport_type in c.WS_TRANSPORTS:
                tcp_remote = f"wss://{tcp_remote}"
            if self.enable_udp:
                udp_remotes.append(f"{node.server}:{node.get_user_port()}")
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
        # merge if rule has same port
        port_map = defaultdict(list)
        for rule in data:
            port_map[rule["listen"]].append(rule)
        data = []
        for port, rules in port_map.items():
            if len(rules) == 1:
                data.append(rules[0])
            else:
                # note that all rules must have same listen_type and transport_type
                first_rule = rules[0]
                tcp_remotes = []
                udp_remotes = []
                labels = []
                for rule in rules:
                    labels.append(rule["label"])
                    tcp_remotes.extend(rule["tcp_remotes"])
                    udp_remotes.extend(rule["udp_remotes"])
                data.append(
                    {
                        "label": "-".join(labels),
                        "listen": port,
                        "listen_type": first_rule["listen_type"],
                        "tcp_remotes": tcp_remotes,
                        "udp_remotes": udp_remotes,
                        "transport_type": first_rule["transport_type"],
                    }
                )
        return {
            "relay_configs": data,
            "web_port": self.web_port,
            "web_token": self.web_token,
            "enable_ping": self.enable_ping,
        }

    @property
    def api_endpoint(self):
        params = {"token": settings.TOKEN}
        return (
            f"{settings.SITE_HOST}/api/ehco_relay_config/{self.id}/?{urlencode(params)}"
        )


class RelayRule(BaseModel):
    rule_name = models.CharField(
        "规则名", max_length=64, blank=True, null=False, default=""
    )
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

    @property
    def relay_host(self):
        return self.relay_node.server

    @property
    def enable(self):
        return self.relay_node.enable and self.proxy_node.enable

    @property
    def enable_udp(self):
        return self.relay_node.enable_udp

    @property
    def remark(self):
        # 这个字段才是用户真正看到的字段,如果不存在就动态生成一个
        if self.rule_name != "":
            return self.rule_name
        name = f"{self.relay_node.name}-{self.proxy_node.name}"
        if self.proxy_node.enlarge_scale != Decimal(1.0):
            name = f"[{self.proxy_node.enlarge_scale}x]{name}"
        return name


class UserTrafficLog(BaseLogModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="用户", null=True
    )
    proxy_node = models.ForeignKey(
        ProxyNode,
        on_delete=models.CASCADE,
        verbose_name="代理节点",
    )
    upload_traffic = models.BigIntegerField("上传流量", default=0)
    download_traffic = models.BigIntegerField("下载流量", default=0)
    ip_list = models.JSONField(verbose_name="IP地址列表", default=list)

    class Meta:
        verbose_name = "用户流量记录"
        verbose_name_plural = "用户流量记录"
        ordering = ["-created_at"]
        index_together = ["user", "proxy_node", "created_at"]

    def __str__(self) -> str:
        return f"用户流量记录:{self.id}"

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
        now = utils.get_current_datetime()
        query = cls.objects.filter(
            proxy_node=proxy_node,
            created_at__range=[now.subtract(seconds=c.NODE_TIME_OUT), now],
        )
        data = {"online_user_count": 0, "online": query.exists()}
        if data["online"]:
            data["online_user_count"] = (
                query.filter(user__isnull=False).values("user").distinct().count()
            )
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


class OccupancyConfig(BaseModel):
    STATUS_ACTIVE = "active"
    STATUS_NORMAL = "normal"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "active"),
        (STATUS_NORMAL, "normal"),
    )
    proxy_node = models.OneToOneField(
        ProxyNode,
        on_delete=models.CASCADE,
        verbose_name="代理节点",
        db_index=True,
        related_name="occupancy_config",
    )
    occupancy_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="价格"
    )
    occupancy_traffic = models.BigIntegerField(default=0, verbose_name="流量(单位字节)")
    occupancy_user_limit = models.PositiveIntegerField(verbose_name="用户数", default=0)
    color = models.CharField(
        choices=c.BULMA_COLOR_CHOICES,
        max_length=32,
        default=c.BULMA_COLOR_EMPTY,
        blank=True,
        verbose_name="颜色",
    )
    status = models.CharField(
        "状态", max_length=32, choices=STATUS_CHOICES, default=STATUS_NORMAL
    )
    remark = models.CharField("备注", max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "占用配置"
        verbose_name_plural = "占用配置"

    def __str__(self) -> str:
        return f"占用配置:{self.id}"

    @classmethod
    def get_purchasable_proxy_nodes(cls, user: User):
        # 1. get all proxy nodes that have occupancy config
        query = cls.objects.filter(occupancy_user_limit__gt=0)
        # 2. filter out nodes that has been occupied by other users
        occupied_node_ids = UserProxyNodeOccupancy.get_occupied_node_ids()
        not_occupied_node_ids = query.exclude(
            proxy_node_id__in=occupied_node_ids
        ).values("proxy_node_id")
        # 3. add nodes that has been occupied by user but not exceed limit
        not_reach_limit_node_ids = []
        for node_query in occupied_node_ids:
            node_id = node_query["proxy_node_id"]
            cfg = cls.objects.get(proxy_node_id=node_id)
            if not cfg.reach_limit(user):
                not_reach_limit_node_ids.append(node_id)
        return ProxyNode.objects.filter(id__in=not_occupied_node_ids).select_related(
            "occupancy_config"
        ) | ProxyNode.objects.filter(id__in=not_reach_limit_node_ids).select_related(
            "occupancy_config"
        )

    def reach_limit(self, user: User):
        node = self.proxy_node
        # 1. check if node has been occupied by user, if yes, return False because user can occupy same node multiple times
        node_user_ids = [
            i["user_id"]
            for i in UserProxyNodeOccupancy.get_node_occupancy_user_ids(node)
        ]
        if user.id in node_user_ids:
            return False
        else:
            return len(node_user_ids) >= self.occupancy_user_limit

    def active_user_count(self):
        node_user_ids = [
            i["user_id"]
            for i in UserProxyNodeOccupancy.get_node_occupancy_user_ids(self.proxy_node)
        ]
        return len(node_user_ids)

    @property
    def human_occupancy_traffic(self):
        return utils.traffic_format(self.occupancy_traffic)

    @property
    def bulma_is_active(self):
        if self.status == self.STATUS_ACTIVE:
            return "is-active"


class UserProxyNodeOccupancy(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    proxy_node = models.ForeignKey(
        ProxyNode, on_delete=models.CASCADE, verbose_name="代理节点"
    )
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始占用时间")
    end_time = models.DateTimeField(null=False, blank=False, verbose_name="结束占用时间")
    used_traffic = models.BigIntegerField("已用流量(单位字节)", default=0)
    total_traffic = models.BigIntegerField("总流量(单位字节)", default=settings.GB)

    class Meta:
        verbose_name = "用户占用记录"
        verbose_name_plural = "用户占用记录"
        indexes = [
            models.Index(fields=["end_time"]),
            models.Index(fields=["user", "end_time"]),
            models.Index(fields=["proxy_node", "end_time"]),
        ]

    def __str__(self) -> str:
        return f"用户占用配置:{self.id}"

    @classmethod
    def _valid_occupancy_query(cls):
        return cls.objects.filter(end_time__gt=utils.get_current_datetime()).filter(
            used_traffic__lt=F("total_traffic")
        )

    @classmethod
    @transaction.atomic
    def create_occupancy(cls, user: User, node: ProxyNode):
        occupancy_config = node.occupancy_config
        # check user limit first
        if occupancy_config.occupancy_user_limit <= 0:
            raise Exception("not allow to create occupancy record with user limit 0")
        if occupancy_config.occupancy_user_limit > 0:
            if (
                cls.get_node_occupancies(node).count()
                >= occupancy_config.occupancy_user_limit
            ):
                raise Exception("occupancy user limit exceed")

        # check user balance
        if user.balance < occupancy_config.occupancy_price:
            raise Exception("user balance not enough")

        user.balance -= occupancy_config.occupancy_price
        user.save()
        # check if user already occupied this node
        o = cls.objects.filter(user=user, proxy_node=node).first()
        if o:
            if o.out_of_usage():
                # reset traffic and time when out of usage
                o.end_time = utils.get_current_datetime().add(days=30)
                o.start_time = utils.get_current_datetime()
                o.used_traffic = 0
                o.total_traffic = occupancy_config.occupancy_traffic
                o.save()
            else:
                # incr traffic and time
                o.end_time = o.end_time + timedelta(days=30)
                o.total_traffic += occupancy_config.occupancy_traffic
                o.save()
        else:
            return cls.objects.create(
                user=user,
                proxy_node=node,
                start_time=utils.get_current_datetime(),
                end_time=utils.get_current_datetime().add(days=30),
                total_traffic=occupancy_config.occupancy_traffic,
            )

    @classmethod
    def get_occupied_node_ids(cls):
        occupied_node_ids = cls._valid_occupancy_query().values("proxy_node_id")
        return occupied_node_ids

    @classmethod
    def get_node_occupancy_user_ids(cls, node: ProxyNode):
        return cls._valid_occupancy_query().filter(proxy_node=node).values("user_id")

    @classmethod
    @classmethod
    def get_user_occupied_node_ids(cls, user: User):
        return cls._valid_occupancy_query().filter(user=user).values("proxy_node_id")

    @classmethod
    def get_node_occupancies(cls, node: ProxyNode):
        return cls._valid_occupancy_query().filter(proxy_node=node)

    @classmethod
    def check_and_incr_traffic(cls, user_id, proxy_node_id, traffic):
        r = cls.objects.get(user__id=user_id, proxy_node__id=proxy_node_id)
        r.used_traffic += traffic
        r.save()

    @classmethod
    def get_user_occupancies(cls, user: User, out_of_usage=False, limit=None):
        # no mater out of usage or not, return all occupancies
        query = cls.objects.filter(user=user)
        if out_of_usage:
            query = query.filter(
                end_time__lt=utils.get_current_datetime()
            ) | query.filter(used_traffic__gte=F("total_traffic"))
        else:
            query = query.filter(end_time__gt=utils.get_current_datetime()).filter(
                used_traffic__lt=F("total_traffic")
            )
        if limit:
            query = query[:limit]
        return query

    def human_total_traffic(self):
        return utils.traffic_format(self.total_traffic)

    def human_used_traffic(self):
        return utils.traffic_format(self.used_traffic)

    def used_percentage(self):
        return round(self.used_traffic / self.total_traffic, 2) * 100

    @property
    def progress_color(self):
        percentage = self.used_percentage()
        if percentage < 20:
            return c.BULMA_COLOR_SUCCESS
        elif percentage < 40:
            return c.BULMA_COLOR_INFO
        elif percentage < 60:
            return c.BULMA_COLOR_LINK
        elif percentage < 80:
            return c.BULMA_COLOR_WARNING
        else:
            return c.BULMA_COLOR_DANGER

    def out_of_usage(self):
        return (
            self.used_traffic >= self.total_traffic
            or self.end_time < utils.get_current_datetime()
        )
