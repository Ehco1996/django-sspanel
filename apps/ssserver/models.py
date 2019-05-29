import base64
import time
from random import choice, randint

import pendulum
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connection, models
from django.db.models import F
from django.forms.models import model_to_dict
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from apps.constants import (
    COUNTRIES_CHOICES,
    METHOD_CHOICES,
    NODE_TIME_OUT,
    OBFS_CHOICES,
    PROTOCOL_CHOICES,
)
from apps.encoder import encoder
from apps.utils import cache, get_current_time, get_short_random_string, traffic_format


class Suser(ExportModelOperationsMixin("ss_user"), models.Model):
    """与user通过user_id作为虚拟外键关联"""

    user_id = models.IntegerField(
        verbose_name="user_id", db_column="user_id", unique=True, db_index=True
    )
    last_check_in_time = models.DateTimeField(
        verbose_name="最后签到时间", null=True, editable=False
    )
    password = models.CharField(
        verbose_name="ss密码",
        max_length=32,
        default=get_short_random_string,
        db_column="passwd",
        validators=[validators.MinLengthValidator(6)],
        unique=True,
    )
    port = models.IntegerField(verbose_name="端口", db_column="port", unique=True)
    last_use_time = models.IntegerField(
        verbose_name="最后使用时间", default=0, editable=False, help_text="时间戳", db_column="t"
    )
    upload_traffic = models.BigIntegerField(
        verbose_name="上传流量", default=0, db_column="u"
    )
    download_traffic = models.BigIntegerField(
        verbose_name="下载流量", default=0, db_column="d"
    )
    transfer_enable = models.BigIntegerField(
        verbose_name="总流量",
        default=settings.DEFAULT_TRAFFIC,
        db_column="transfer_enable",
    )
    speed_limit = models.IntegerField(
        verbose_name="限速", default=0, db_column="speed_limit"
    )
    switch = models.BooleanField(
        verbose_name="保留字段switch", default=True, db_column="switch"
    )
    enable = models.BooleanField(verbose_name="开启与否", default=True, db_column="enable")
    method = models.CharField(
        verbose_name="加密类型",
        default=settings.DEFAULT_METHOD,
        max_length=32,
        choices=METHOD_CHOICES,
    )
    protocol = models.CharField(
        verbose_name="协议",
        default=settings.DEFAULT_PROTOCOL,
        max_length=32,
        choices=PROTOCOL_CHOICES,
    )
    protocol_param = models.CharField(
        verbose_name="协议参数", max_length=128, null=True, blank=True
    )
    obfs = models.CharField(
        verbose_name="混淆",
        default=settings.DEFAULT_OBFS,
        max_length=32,
        choices=OBFS_CHOICES,
    )
    obfs_param = models.CharField(
        verbose_name="混淆参数", max_length=255, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = "Ss用户"
        ordering = ("-last_check_in_time",)
        db_table = "s_user"

    def __str__(self):
        return self.user.username

    def clean(self):
        """保证端口在1024<50000之间"""
        if self.port:
            if not 1024 < self.port < 50000:
                raise ValidationError("端口必须在1024和50000之间")

    @classmethod
    def create_by_user_id(cls, user_id):
        return cls.objects.create(user_id=user_id, port=cls.get_random_port())

    @classmethod
    def get_user_by_user_id(cls, user_id):
        return cls.objects.get(user_id=user_id)

    @classmethod
    def get_today_checked_user_num(cls):
        now = get_current_time()
        midnight = pendulum.datetime(
            year=now.year, month=now.month, day=now.day, tz=now.tz
        )
        query = cls.objects.filter(last_check_in_time__gte=midnight)
        return query.count()

    @classmethod
    def get_never_checked_user_num(cls):
        return cls.objects.filter(last_check_in_time=None).count()

    @classmethod
    def get_never_used_num(cls):
        """返回从未使用过的人数"""
        return cls.objects.filter(last_use_time=0).count()

    @classmethod
    def get_user_order_by_traffic(cls, count=10):
        return cls.objects.all().order_by("-download_traffic")[:count]

    @classmethod
    def get_ss_users_by_level(cls, level):
        """返回指大于等于指定等级的所有合法用户"""
        from apps.sspanel.models import User

        user_ids = User.objects.filter(level__gte=level).values_list("id")
        users = cls.objects.filter(
            transfer_enable__gte=(F("upload_traffic") + F("download_traffic")),
            user_id__in=user_ids,
        )
        return users

    @classmethod
    @cache.cached(ttl=60 * 60 * 5)
    def get_user_configs_by_node_id(cls, node_id):
        from apps.sspanel.models import SSNode

        # TODO 1. 下线SSR节点后处理这里 2. 优化Cache
        data = []
        node = SSNode.get_or_none_by_node_id(node_id)
        if not node:
            # FALLBACK TO SSRNODE
            node = Node.get_or_none_by_node_id(node_id)
        if not node:
            return data
        for ss_user in cls.get_ss_users_by_level(node.level):
            data.append(node.to_dict_with_ss_user(ss_user))
        return data

    @classmethod
    def clear_get_user_configs_by_node_id_cache(cls, node_ids=None):
        if not node_ids:
            node_ids = Node.get_node_ids_by_show(all=True)
        keys = []
        for node_id in node_ids:
            keys.append(cls.get_user_configs_by_node_id.make_cache_key(cls, node_id))
        return cache.delete_many(keys)

    @classmethod
    def get_random_port(cls):
        users = cls.objects.all().values_list("port")
        port_list = []
        for user in users:
            port_list.append(user[0])
        if len(port_list) == 0:
            return 1025
        all_ports = [i for i in range(1025, max(port_list) + 1)]
        try:
            return choice(list(set(all_ports).difference(set(port_list))))
        except IndexError:
            return max(port_list) + 1

    @property
    def user(self):
        from apps.sspanel.models import User

        return User.objects.get(pk=self.user_id)

    @property
    def today_is_checked(self):
        if self.last_check_in_time:
            return self.last_check_in_time.date() == timezone.now().date()
        return False

    @property
    def user_last_use_time(self):
        t = pendulum.from_timestamp(self.last_use_time, tz=settings.TIME_ZONE)
        return t

    @property
    def used_traffic(self):
        return traffic_format(self.download_traffic + self.upload_traffic)

    @property
    def total_transfer(self):
        return traffic_format(self.transfer_enable)

    @property
    def unused_traffic(self):
        return traffic_format(
            self.transfer_enable - self.upload_traffic - self.download_traffic
        )

    @property
    def used_percentage(self):
        try:
            used = self.download_traffic + self.upload_traffic
            return used / self.transfer_enable * 100
        except ZeroDivisionError:
            return 100

    @property
    def token(self):
        return encoder.int2string(self.user_id)

    def checkin(self):
        if not self.today_is_checked:
            traffic = randint(
                settings.MIN_CHECKIN_TRAFFIC, settings.MAX_CHECKIN_TRAFFIC
            )
            self.transfer_enable += traffic
            self.last_check_in_time = get_current_time()
            self.save()
            return True, traffic
        return False, 0

    def reset_traffic(self, new_traffic):
        self.transfer_enable = new_traffic
        self.upload_traffic = 0
        self.download_traffic = 0

    def reset_to_fresh(self):
        self.enable = False
        self.reset_traffic(settings.DEFAULT_TRAFFIC)
        self.save()

    def increase_transfer(self, new_transfer):
        self.transfer_enable += new_transfer

    def update_from_dict(self, data):
        clean_fields = ["password", "method", "protocol", "obfs"]
        for k, v in data.items():
            if k in clean_fields:
                setattr(self, k, v)
        try:
            self.full_clean()
            self.save()
            Suser.clear_get_user_configs_by_node_id_cache()
            return True
        except ValidationError:
            return False

    def get_import_links(self):
        from apps.sspanel.models import SSNode

        links = [node.get_ss_link(self) for node in SSNode.get_active_nodes()]
        return "\n".join(links)


class Node(ExportModelOperationsMixin("node"), models.Model):
    """线路节点"""

    SHOW_CHOICES = ((1, "显示"), (-1, "不显示"))

    NODE_TYPE_CHOICES = ((0, "多端口多用户"), (1, "单端口多用户"))

    CUSTOM_METHOD_CHOICES = ((0, "否"), (1, "是"))

    SS_TYPE_CHOICES = ((0, "SS"), (1, "SSR"), (2, "SS/SSR"))

    node_id = models.IntegerField("节点id", unique=True)
    port = models.IntegerField("节点端口", default=443, blank=True, help_text="单端口多用户时需要")
    password = models.CharField(
        "节点密码", max_length=32, default="password", help_text="单端口时需要"
    )
    country = models.CharField(
        "国家", default="CN", max_length=2, choices=COUNTRIES_CHOICES
    )
    custom_method = models.SmallIntegerField(
        "自定义加密", choices=CUSTOM_METHOD_CHOICES, default=0
    )
    show = models.SmallIntegerField("是否显示", choices=SHOW_CHOICES, default=1)
    node_type = models.SmallIntegerField("节点类型", choices=NODE_TYPE_CHOICES, default=0)
    ss_type = models.SmallIntegerField("SS类型", choices=SS_TYPE_CHOICES, default=2)
    name = models.CharField("名字", max_length=32)
    info = models.CharField("节点说明", max_length=1024, blank=True, null=True)
    server = models.CharField("服务器IP", max_length=128)
    method = models.CharField(
        "加密类型", default=settings.DEFAULT_METHOD, max_length=32, choices=METHOD_CHOICES
    )
    traffic_rate = models.FloatField("流量比例", default=1.0)
    protocol = models.CharField(
        "协议", default=settings.DEFAULT_PROTOCOL, max_length=32, choices=PROTOCOL_CHOICES
    )
    protocol_param = models.CharField("协议参数", max_length=128, default="", blank=True)
    obfs = models.CharField(
        "混淆", default=settings.DEFAULT_OBFS, max_length=32, choices=OBFS_CHOICES
    )
    obfs_param = models.CharField("混淆参数", max_length=255, default="", blank=True)
    level = models.PositiveIntegerField(
        "节点等级", default=0, validators=[MaxValueValidator(9), MinValueValidator(0)]
    )
    total_traffic = models.BigIntegerField("总流量", default=settings.GB)
    used_traffic = models.BigIntegerField("已用流量", default=0)
    speed_limit = models.IntegerField("限速", default=0)
    order = models.PositiveSmallIntegerField("排序", default=1)
    group = models.CharField("分组名", max_length=32, default="谜之屋")

    class Meta:
        ordering = ["-show", "order"]
        verbose_name_plural = "节点"
        db_table = "ss_node"

    def __str__(self):
        return self.name

    @classmethod
    def get_or_none_by_node_id(cls, node_id):
        return cls.objects.filter(node_id=node_id).first()

    @classmethod
    def get_by_node_id(cls, node_id):
        return cls.objects.get(node_id=node_id)

    @classmethod
    def get_node_ids_by_show(cls, show=1, all=False):
        if all:
            nodes = cls.objects.all().values_list("node_id")
        else:
            nodes = cls.objects.filter(show=show).values_list("node_id")
        return [node[0] for node in nodes]

    @classmethod
    def get_active_nodes(cls):
        return cls.objects.filter(show=1, ss_type=1).order_by("order")

    def get_ssr_link(self, ss_user):
        """返回ssr链接"""
        ssr_password = (
            base64.urlsafe_b64encode(bytes(ss_user.password, "utf8"))
            .decode("utf8")
            .replace("=", "")
        )
        ssr_remarks = (
            base64.urlsafe_b64encode(bytes(self.name, "utf8"))
            .decode("utf8")
            .replace("=", "")
        )
        ssr_group = (
            base64.urlsafe_b64encode(bytes(self.group, "utf8"))
            .decode("utf8")
            .replace("=", "")
        )
        if self.node_type == 1:
            # 单端口多用户
            ssr_password = (
                base64.urlsafe_b64encode(bytes(self.password, "utf8"))
                .decode("utf8")
                .replace("=", "")
            )
            info = "{}:{}".format(ss_user.port, ss_user.password)
            protocol_param = (
                base64.urlsafe_b64encode(bytes(info, "utf8"))
                .decode("utf8")
                .replace("=", "")
            )
            obfs_param = (
                base64.urlsafe_b64encode(bytes(str(self.obfs_param), "utf8"))
                .decode("utf8")
                .replace("=", "")
            )
            ssr_code = "{}:{}:{}:{}:{}:{}/?obfsparam={}&protoparam={}&remarks={}&group={}".format(
                self.server,
                self.port,
                self.protocol,
                self.method,
                self.obfs,
                ssr_password,
                obfs_param,
                protocol_param,
                ssr_remarks,
                ssr_group,
            )
        elif self.custom_method == 1:
            ssr_code = "{}:{}:{}:{}:{}:{}/?remarks={}&group={}".format(
                self.server,
                ss_user.port,
                ss_user.protocol,
                ss_user.method,
                ss_user.obfs,
                ssr_password,
                ssr_remarks,
                ssr_group,
            )
        else:
            ssr_code = "{}:{}:{}:{}:{}:{}/?remarks={}&group={}".format(
                self.server,
                ss_user.port,
                self.protocol,
                self.method,
                self.obfs,
                ssr_password,
                ssr_remarks,
                ssr_group,
            )
        ssr_pass = (
            base64.urlsafe_b64encode(bytes(ssr_code, "utf8"))
            .decode("utf8")
            .replace("=", "")
        )
        ssr_link = "ssr://{}".format(ssr_pass)
        return ssr_link

    def get_ss_link(self, ss_user):
        """返回ss链接"""
        if self.custom_method == 1:
            ss_code = "{}:{}@{}:{}".format(
                ss_user.method, ss_user.password, self.server, ss_user.port
            )
        else:
            ss_code = "{}:{}@{}:{}".format(
                self.method, ss_user.password, self.server, ss_user.port
            )
        ss_pass = base64.urlsafe_b64encode(bytes(ss_code, "utf8")).decode("utf8")
        ss_link = "ss://{}#{}".format(ss_pass, self.name)
        return ss_link

    def save(self, *args, **kwargs):
        if self.node_type == 1:
            self.custom_method = 0
        super(Node, self).save(*args, **kwargs)

    def human_total_traffic(self):
        """总流量"""
        return traffic_format(self.total_traffic)

    def human_used_traffic(self):
        """已用流量"""
        return traffic_format(self.used_traffic)

    def to_dict_with_ss_user(self, ss_user):
        data = model_to_dict(self)
        data.update(model_to_dict(ss_user))
        if not self.custom_method:
            data["method"] = self.method
        if self.node_type == 1:
            data["method"] = self.method
            data["protocol_param"] = "{}:{}".format(ss_user.port, ss_user.password)
        data["id"] = ss_user.user_id
        return data

    def to_dict_with_extra_info(self, ss_user):
        from apps.sspanel.models import SSNodeOnlineLog

        data = self.to_dict_with_ss_user(ss_user)
        data.update(SSNodeOnlineLog.get_latest_online_log_info(self.node_id))
        data["country"] = self.country.lower()
        data["ss_link"] = self.get_ss_link(ss_user)
        return data

    # verbose_name
    human_total_traffic.short_description = "总流量"
    human_used_traffic.short_description = "使用流量"
