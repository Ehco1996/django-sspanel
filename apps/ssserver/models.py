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
    def get_users_by_level(cls, level):
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
        data = []
        node = Node.objects.filter(node_id=node_id, show=1).first()
        if not node:
            return data
        user_list = cls.get_users_by_level(node.level)
        for user in user_list:
            cfg = {
                "port": user.port,
                "u": user.upload_traffic,
                "d": user.download_traffic,
                "transfer_enable": user.transfer_enable,
                "passwd": user.password,
                "enable": user.enable,
                "user_id": user.user_id,
                "id": user.user_id,
                "token": user.token,
                "method": user.method,
                "obfs": user.obfs,
                "obfs_param": user.obfs_param,
                "protocol": user.protocol,
                "protocol_param": user.protocol_param,
                "speed_limit_per_user": user.speed_limit,
            }
            if node.speed_limit > 0:
                if user.speed_limit > 0:
                    cfg["speed_limit_per_user"] = min(
                        user.speed_limit, node.speed_limit
                    )
                else:
                    cfg["speed_limit_per_user"] = node.speed_limit

            data.append(cfg)
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
    def get_by_node_id(cls, node_id):
        return cls.objects.get(node_id=node_id)

    @classmethod
    def get_import_code(cls, user):
        """获取该用户的所有节点的导入信息"""
        ss_user = user.ss_user
        sub_code_list = []
        node_list = cls.objects.filter(level__lte=user.level, show=1)
        for node in node_list:
            sub_code_list.append(node.get_node_link(ss_user))
        return "\n".join(sub_code_list)

    @classmethod
    def get_node_ids_by_show(cls, show=1, all=False):
        if all:
            nodes = cls.objects.all().values_list("node_id")
        else:
            nodes = cls.objects.filter(show=show).values_list("node_id")
        return [node[0] for node in nodes]

    @classmethod
    def get_active_nodes(cls):
        return cls.objects.filter(show=1)

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

    def get_node_link(self, ss_user):
        """获取当前的节点链接"""
        if self.ss_type == 0:
            return self.get_ss_link(ss_user)
        else:
            return self.get_ssr_link(ss_user)

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

    # verbose_name
    human_total_traffic.short_description = "总流量"
    human_used_traffic.short_description = "使用流量"


class TrafficLog(ExportModelOperationsMixin("traffic_log"), models.Model):
    """用户流量记录"""

    user_id = models.IntegerField("用户id", blank=False, null=False, db_index=True)
    node_id = models.IntegerField("节点id", blank=False, null=False, db_index=True)
    upload_traffic = models.BigIntegerField("上传流量", default=0, db_column="u")
    download_traffic = models.BigIntegerField("下载流量", default=0, db_column="d")
    rate = models.FloatField("流量比例", default=1.0, null=False)
    traffic = models.CharField("流量记录", max_length=32, null=False)
    log_time = models.IntegerField("日志时间", blank=False, null=False)
    log_date = models.DateField(
        "记录日期", default=timezone.now, blank=False, null=False, db_index=True
    )

    def __str__(self):
        return self.traffic

    class Meta:
        verbose_name_plural = "流量记录"
        ordering = ("-log_time",)
        db_table = "user_traffic_log"

    @property
    def user(self):
        from apps.sspanel.models import User

        return User.objects.get(pk=self.user_id)

    @property
    def used_traffic(self):
        return self.download_traffic + self.upload_traffic

    @classmethod
    def calc_user_total_traffic(cls, node_id, user_id):
        logs = cls.objects.filter(node_id=node_id, user_id=user_id)
        aggs = logs.aggregate(
            u=models.Sum("upload_traffic"), d=models.Sum("download_traffic")
        )
        ut = aggs["u"] if aggs["u"] else 0
        dt = aggs["d"] if aggs["d"] else 0
        return traffic_format(ut + dt)

    @classmethod
    def calc_user_traffic_by_date(cls, user_id, node_id, date):
        logs = cls.objects.filter(node_id=node_id, user_id=user_id, log_date=date)
        aggs = logs.aggregate(
            u=models.Sum("upload_traffic"), d=models.Sum("download_traffic")
        )
        ut = aggs["u"] if aggs["u"] else 0
        dt = aggs["d"] if aggs["d"] else 0
        return (ut + dt) // settings.MB

    @classmethod
    def gen_line_chart_configs(cls, user_id, node_id, date_list):
        node = Node.get_by_node_id(node_id)
        user_total_traffic = cls.calc_user_total_traffic(node_id, user_id)
        date_list = sorted(date_list)
        line_config = {
            "title": "节点 {} 当月共消耗：{}".format(node.name, user_total_traffic),
            "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
            "data": [
                cls.calc_user_traffic_by_date(user_id, node_id, date)
                for date in date_list
            ],
            "data_title": node.name,
            "x_label": "日期 最近七天",
            "y_label": "流量 单位：MB",
        }
        return line_config

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE {}".format(cls._meta.db_table))


class NodeOnlineLog(ExportModelOperationsMixin("node_online_log"), models.Model):
    """节点在线记录"""

    node_id = models.IntegerField("节点id", blank=False, null=False)
    online_user = models.IntegerField("在线人数", blank=False, null=False)
    log_time = models.IntegerField("日志时间", blank=False, null=False)

    class Meta:
        verbose_name_plural = "节点在线记录"
        db_table = "ss_node_online_log"

    def __str__(self):
        return "节点：{}".format(self.node_id)

    @classmethod
    def get_online_user_count(cls):
        count = 0
        for node_id in Node.get_node_ids_by_show():
            o = cls.objects.filter(node_id=node_id).order_by("-log_time")[:1]
            if o:
                count += o[0].get_online_user()
        return count

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE {}".format(cls._meta.db_table))

    def get_oneline_status(self):
        """检测是否在线"""
        if int(time.time()) - self.log_time > NODE_TIME_OUT:
            return False
        else:
            return True

    def get_online_user(self):
        """返回在线人数"""
        if self.get_oneline_status():
            return self.online_user
        else:
            return 0


class AliveIp(ExportModelOperationsMixin("aliveip_log"), models.Model):

    node_id = models.IntegerField(verbose_name="节点id", blank=False, null=False)
    ip = models.CharField(verbose_name="设备ip", max_length=128)
    user = models.CharField(verbose_name="用户名", max_length=128)
    log_time = models.DateTimeField("日志时间", auto_now=True)

    class Meta:
        verbose_name_plural = "节点在线IP"
        ordering = ["-log_time"]

    @classmethod
    def recent_alive(cls, node_id):
        """
        返回节点最近一分钟的在线ip
        """
        ret = []
        seen = []
        now = pendulum.now()
        last_now = now.subtract(minutes=1)
        time_range = [str(last_now), str(now)]
        logs = cls.objects.filter(node_id=node_id, log_time__range=time_range)
        for log in logs:
            if log.ip not in seen:
                seen.append(log.ip)
                ret.append(log)
        return ret

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE {}".format(cls._meta.db_table))

    @property
    def node_name(self):
        return Node.get_by_node_id(self.node_id).name
