import datetime
import random
import re
import time
from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4

import markdown
import pendulum
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connection, models, transaction
from django.utils import functional, timezone
from redis.exceptions import LockError

from apps import constants as c
from apps.ext import encoder, lock, pay
from apps.utils import (
    get_current_datetime,
    get_long_random_string,
    get_short_random_string,
    traffic_format,
)


class User(AbstractUser):

    MIN_PORT = 1025
    PORT_BLACK_SET = {6443, 8472}

    class Meta(AbstractUser.Meta):
        verbose_name_plural = "用户"

    balance = models.DecimalField(
        verbose_name="余额",
        decimal_places=2,
        max_digits=10,
        default=0,
        editable=True,
        null=True,
        blank=True,
    )
    invitecode_num = models.PositiveIntegerField(
        verbose_name="可生成的邀请码数量", default=settings.INVITE_NUM
    )
    level = models.PositiveIntegerField(
        verbose_name="用户等级", default=0, validators=[MinValueValidator(0)]
    )
    level_expire_time = models.DateTimeField(verbose_name="等级有效期", default=timezone.now)
    theme = models.CharField(
        verbose_name="主题",
        choices=c.THEME_CHOICES,
        default=settings.DEFAULT_THEME,
        max_length=10,
    )
    inviter_id = models.PositiveIntegerField(verbose_name="邀请人id", default=1)

    # ss 相关
    ss_port = models.IntegerField("端口", unique=True, default=MIN_PORT)
    ss_password = models.CharField(
        "密码", max_length=32, default=get_short_random_string, unique=True
    )
    # v2ray相关
    vmess_uuid = models.CharField(verbose_name="Vmess uuid", max_length=64, default="")
    # 流量相关
    upload_traffic = models.BigIntegerField("上传流量", default=0)
    download_traffic = models.BigIntegerField("下载流量", default=0)
    total_traffic = models.BigIntegerField("总流量", default=settings.DEFAULT_TRAFFIC)
    last_use_time = models.DateTimeField("上次使用时间", blank=True, db_index=True, null=True)

    def __str__(self):
        return self.username

    @classmethod
    def get_total_user_num(cls):
        """返回用户总数"""
        return cls.objects.all().count()

    @classmethod
    def get_today_register_user(cls):
        """返回今日注册的用户"""
        return cls.objects.filter(date_joined__gt=pendulum.today())

    @classmethod
    @transaction.atomic
    def add_new_user(cls, cleaned_data):
        user = cls.objects.create_user(
            cleaned_data["username"],
            cleaned_data["email"],
            cleaned_data["password1"],
            ss_port=cls.get_not_used_port(),
        )
        inviter_id = None
        if "invitecode" in cleaned_data:
            code = InviteCode.objects.get(code=cleaned_data["invitecode"])
            code.consume()
            inviter_id = code.user_id
        elif "ref" in cleaned_data:
            inviter_id = cleaned_data["ref"]
        if inviter_id:
            # 绑定邀请人
            UserRefLog.log_ref(inviter_id, pendulum.today())
            user.inviter_id = inviter_id
        # 绑定uuid
        user.vmess_uuid = str(uuid4())
        user.save()
        return user

    @classmethod
    def get_by_user_name(cls, username):
        return cls.objects.get(username=username)

    @classmethod
    def get_by_pk(cls, pk):
        return cls.objects.get(pk=pk)

    @classmethod
    def get_or_none(cls, pk):
        return cls.objects.filter(pk=pk).first()

    @classmethod
    def check_and_disable_expired_users(cls):
        now = get_current_datetime()
        expired_users = list(
            cls.objects.filter(level__gt=0, level_expire_time__lte=now)
        )
        for user in expired_users:
            user.level = 0
            user.save()
            print(f"Time: {now} user: {user} level timeout!")
        if expired_users and settings.EXPIRE_EMAIL_NOTICE:
            EmailSendLog.send_mail_to_users(
                expired_users,
                f"您的{settings.TITLE}账号已到期",
                f"您的账号现被暂停使用。如需继续使用请前往 {settings.HOST} 充值",
            )

    @classmethod
    def check_and_disable_out_of_traffic_user(cls):
        # NOTE cronjob用 先不加索引
        out_of_traffic_users = list(
            cls.objects.filter(
                level__gt=0,
                total_traffic__lte=(
                    models.F("upload_traffic") + models.F("download_traffic")
                ),
            )
        )
        for user in out_of_traffic_users:
            user.level = 0
            user.save()
            print(f"user: {user} traffic overflow!")

        if out_of_traffic_users and settings.EXPIRE_EMAIL_NOTICE:
            EmailSendLog.send_mail_to_users(
                out_of_traffic_users,
                f"您的{settings.TITLE}账号流量已全部用完",
                f"您的账号现被暂停使用。如需继续使用请前往 {settings.HOST} 充值",
            )
            print(f"共有{len(out_of_traffic_users)}个用户流量用超啦")

    @classmethod
    def get_not_used_port(cls):
        port_set = {log["ss_port"] for log in cls.objects.all().values("ss_port")}
        if not port_set:
            return cls.MIN_PORT
        max_port = max(port_set) + 1
        port_set = {i for i in range(cls.MIN_PORT, max_port + 1)}.difference(
            port_set.union(cls.PORT_BLACK_SET)
        )
        return random.choice(list(port_set))

    @classmethod
    def get_never_used_user_count(cls):
        return cls.objects.filter(last_use_time__isnull=True).count()

    @classmethod
    def get_user_order_by_traffic(cls, count=10):
        # NOTE 后台展示用 暂时不加索引
        return cls.objects.all().order_by("-download_traffic")[:count]

    @property
    def sub_link(self):
        """订阅地址"""
        params = {"token": self.token}
        return settings.HOST + f"/api/subscribe/?{urlencode(params)}"

    @property
    def ref_link(self):
        """ref地址"""
        params = {"ref": self.id}
        return settings.HOST + f"/register/?{urlencode(params)}"

    @property
    def today_is_checkin(self):
        return UserCheckInLog.get_today_is_checkin_by_user_id(self.pk)

    @property
    def token(self):
        return encoder.int2string(self.pk)

    @property
    def human_total_traffic(self):
        return traffic_format(self.total_traffic)

    @property
    def human_used_traffic(self):
        return traffic_format(self.used_traffic)

    @property
    def human_remain_traffic(self):
        return traffic_format(self.total_traffic - self.used_traffic)

    @property
    def overflow(self):
        return (self.upload_traffic + self.download_traffic) > self.total_traffic

    @property
    def used_traffic(self):
        return self.upload_traffic + self.download_traffic

    @property
    def used_percentage(self):
        try:
            return round(self.used_traffic / self.total_traffic * 100, 2)
        except ZeroDivisionError:
            return 100.00

    @property
    def remain_percentage(self):
        return 100.00 - self.used_percentage

    @transaction.atomic
    def reset_random_port(self):
        cls = type(self)
        port = cls.get_not_used_port()
        self.port = port
        self.save()
        return port

    def update_ss_config_from_dict(self, data):
        clean_fields = ["ss_password"]
        for k, v in data.items():
            if k in clean_fields:
                setattr(self, k, v)
        try:
            self.full_clean()
            self.save()
            return True
        except ValidationError:
            return False

    def reset_traffic(self, new_traffic):
        self.total_traffic = new_traffic
        self.upload_traffic = 0
        self.download_traffic = 0

    def reset_to_fresh(self):
        self.enable = False
        self.reset_traffic(settings.DEFAULT_TRAFFIC)
        self.save()


class UserPropertyMixin:
    @functional.cached_property
    def user(self):
        return User.get_by_pk(self.user_id)


class UserOrder(models.Model, UserPropertyMixin):

    ALIPAY_CALLBACK_URL = f"{settings.HOST}/api/callback/alipay"
    DEFAULT_ORDER_TIME_OUT = "10m"
    STATUS_CREATED = 0
    STATUS_PAID = 1
    STATUS_FINISHED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, "created"),
        (STATUS_PAID, "paid"),
        (STATUS_FINISHED, "finished"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    status = models.SmallIntegerField(
        verbose_name="订单状态", db_index=True, choices=STATUS_CHOICES
    )
    out_trade_no = models.CharField(
        verbose_name="流水号", max_length=64, unique=True, db_index=True
    )
    qrcode_url = models.CharField(verbose_name="支付连接", max_length=512, null=True)
    amount = models.DecimalField(
        verbose_name="金额", decimal_places=2, max_digits=10, default=0
    )
    created_at = models.DateTimeField(
        verbose_name="时间", auto_now_add=True, db_index=True
    )
    expired_at = models.DateTimeField(verbose_name="过期时间", db_index=True)

    def __str__(self):
        return f"<{self.id,self.user}>:{self.amount}"

    class Meta:
        verbose_name_plural = "用户订单"
        index_together = ["user", "status"]

    @classmethod
    def gen_out_trade_no(cls):
        return datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S%s")

    @classmethod
    def get_not_paid_order_by_amount(cls, user, amount):
        return (
            cls.objects.filter(user=user, status=cls.STATUS_CREATED, amount=amount)
            .order_by("-created_at")
            .first()
        )

    @classmethod
    def get_or_create_order(cls, user, amount):
        # NOTE 目前这里只支持支付宝 所以暂时写死
        with lock.user_create_order_lock(user.id):
            now = get_current_datetime()
            order = cls.get_not_paid_order_by_amount(user, amount)
            if order and order.expired_at > now:
                return order
            with transaction.atomic():
                out_trade_no = cls.gen_out_trade_no()
                trade = pay.trade_precreate(
                    out_trade_no=out_trade_no,
                    total_amount=amount,
                    subject=settings.ALIPAY_TRADE_INFO.format(amount),
                    timeout_express=cls.DEFAULT_ORDER_TIME_OUT,
                    notify_url=cls.ALIPAY_CALLBACK_URL,
                )
                qrcode_url = trade.get("qr_code")
                order = cls.objects.create(
                    user=user,
                    status=cls.STATUS_CREATED,
                    out_trade_no=out_trade_no,
                    amount=amount,
                    qrcode_url=qrcode_url,
                    expired_at=now.add(minutes=10),
                )
                return order

    @classmethod
    def get_and_check_recent_created_order(cls, user):
        order = cls.objects.filter(user=user).order_by("-created_at").first()
        if order is None:
            return
        with lock.order_lock(order.out_trade_no):
            order.refresh_from_db()
            with transaction.atomic():
                order.check_order_status()
        return order

    @classmethod
    def make_up_lost_orders(cls):
        now = get_current_datetime()
        for order in cls.objects.filter(status=cls.STATUS_CREATED, expired_at__gte=now):
            try:
                with lock.order_lock(order.out_trade_no):
                    order.refresh_from_db()
                    changed = order.check_order_status()
                    if changed:
                        print(f"补单：{order.user}={order.amount}")
            except LockError:
                # NOTE 定时任务跑，抢不到锁就算了吧
                pass

    @classmethod
    def handle_callback_by_alipay(cls, data):
        order = UserOrder.objects.get(out_trade_no=data["out_trade_no"])
        with lock.order_lock(order.out_trade_no):
            order.refresh_from_db()
            if order.status != order.STATUS_CREATED:
                return True
            signature = data.pop("sign")
            res = pay.verify(data, signature)
            success = res and data["trade_status"] in (
                "TRADE_SUCCESS",
                "TRADE_FINISHED",
            )
            with transaction.atomic():
                if success:
                    order.status = order.STATUS_PAID
                    order.save()
                order.handle_paid()
            return success

    def handle_paid(self):
        # NOTE Must use in transaction
        self.refresh_from_db()
        if self.status != self.STATUS_PAID:
            return
        self.user.balance += self.amount
        self.user.save()
        self.status = self.STATUS_FINISHED
        self.save()
        # 将充值记录和捐赠绑定
        Donate.objects.create(user=self.user, money=self.amount)

    def check_order_status(self):
        changed = False
        if self.status != self.STATUS_CREATED:
            return changed
        res = pay.trade_query(out_trade_no=self.out_trade_no)
        if res.get("trade_status", "") == "TRADE_SUCCESS":
            self.status = self.STATUS_PAID
            self.save()
            changed = True
        self.handle_paid()
        return changed


class UserRefLog(models.Model, UserPropertyMixin):
    user_id = models.PositiveIntegerField()
    register_count = models.IntegerField(default=0)
    date = models.DateField("记录日期", default=pendulum.today, db_index=True)

    class Meta:
        verbose_name_plural = "用户推荐记录"
        unique_together = [["user_id", "date"]]

    @classmethod
    def log_ref(cls, user_id, date):
        log, _ = cls.objects.get_or_create(user_id=user_id, date=date)
        log.register_count += 1
        log.save()

    @classmethod
    def list_by_user_id_and_date_list(cls, user_id, date_list):
        return cls.objects.filter(user_id=user_id, date__in=date_list)

    @classmethod
    def gen_bar_chart_configs(cls, user_id, date_list):
        """set register_count to 0 if the query date log not exists"""
        date_list = sorted(date_list)
        logs = {
            log.date: log.register_count
            for log in cls.list_by_user_id_and_date_list(user_id, date_list)
        }
        bar_config = {
            "labels": [f"{date.month}-{date.day}" for date in date_list],
            "data": [logs.get(date, 0) for date in date_list],
            "data_title": "每日邀请注册人数",
        }
        return bar_config


class UserOnLineIpLog(models.Model, UserPropertyMixin):

    user_id = models.IntegerField(db_index=True)
    node_id = models.IntegerField()
    ip = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "用户在线IP"
        ordering = ["-created_at"]
        index_together = ["node_id", "created_at"]

    @classmethod
    def get_recent_log_by_node_id(cls, node_id):
        now = get_current_datetime()
        ip_set = set()
        ret = []
        for log in cls.objects.filter(
            node_id=node_id,
            created_at__range=[now.subtract(seconds=c.NODE_TIME_OUT), now],
        ):
            if log.ip not in ip_set:
                ret.append(log)
            ip_set.add(log.ip)
        return ret

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE {}".format(cls._meta.db_table))


class UserCheckInLog(models.Model, UserPropertyMixin):
    user_id = models.PositiveIntegerField()
    date = models.DateField("记录日期", default=pendulum.today, db_index=True)
    increased_traffic = models.BigIntegerField("增加的流量", default=0)

    class Meta:
        verbose_name_plural = "用户签到记录"
        unique_together = [["user_id", "date"]]

    @classmethod
    def add_log(cls, user_id, traffic):
        return cls.objects.create(user_id=user_id, increased_traffic=traffic)

    @classmethod
    @transaction.atomic
    def checkin(cls, user):
        traffic = random.randint(
            settings.MIN_CHECKIN_TRAFFIC, settings.MAX_CHECKIN_TRAFFIC
        )
        user.total_traffic += traffic
        user.save()
        return cls.add_log(user.id, traffic)

    @classmethod
    def get_today_is_checkin_by_user_id(cls, user_id):
        return cls.objects.filter(user_id=user_id, date=pendulum.today()).exists()

    @classmethod
    def get_today_checkin_user_count(cls):
        return cls.objects.filter(date=pendulum.today()).count()

    @property
    def human_increased_traffic(self):
        return traffic_format(self.increased_traffic)


# TODO del those model 下面几张表都挪走啦，过段时间删掉，留在这里是怕需要迁移数据


class NodeOnlineLog(models.Model):
    # NOTE add trojan
    NODE_TYPE_SS = "ss"
    NODE_TYPE_VMESS = "vmess"
    NODE_TYPE_TROJAN = "trojan"
    NODE_CHOICES = (
        (NODE_TYPE_SS, NODE_TYPE_SS),
        (NODE_TYPE_VMESS, NODE_TYPE_VMESS),
        (NODE_TYPE_TROJAN, NODE_TYPE_TROJAN),
    )

    node_id = models.IntegerField()
    node_type = models.CharField(
        "节点类型", default=NODE_TYPE_SS, choices=NODE_CHOICES, max_length=32
    )
    online_user_count = models.IntegerField(default=0)
    active_tcp_connections = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "节点在线记录"
        ordering = ["-created_at"]
        index_together = ["node_type", "node_id", "created_at"]


class BaseAbstractNode(models.Model):

    node_id = models.IntegerField(unique=True)
    level = models.PositiveIntegerField(default=0)
    name = models.CharField("名字", max_length=32)
    info = models.CharField("节点说明", max_length=1024)
    country = models.CharField(
        "国家", default="CN", max_length=5, choices=c.COUNTRIES_CHOICES
    )
    used_traffic = models.BigIntegerField("已用流量", default=0)
    total_traffic = models.BigIntegerField("总流量", default=settings.GB)
    enable = models.BooleanField("是否开启", default=True, db_index=True)
    enlarge_scale = models.DecimalField(
        "倍率", default=Decimal("1.0"), decimal_places=2, max_digits=10,
    )

    ehco_listen_host = models.CharField("隧道监听地址", max_length=64, blank=True, null=True)
    ehco_listen_port = models.CharField("隧道监听端口", max_length=64, blank=True, null=True)
    ehco_listen_type = models.CharField(
        "隧道监听类型", max_length=64, choices=c.LISTEN_TYPES, default=c.LISTEN_RAW
    )
    ehco_transport_type = models.CharField(
        "隧道传输类型", max_length=64, choices=c.TRANSPORT_TYPES, default=c.TRANSPORT_RAW
    )
    enable_ehco_lb = models.BooleanField("是否负载均衡", default=True, db_index=True)

    class Meta:
        abstract = True


class RelayNode(BaseAbstractNode):

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

    #  去除一些不需要的字段
    info = None
    used_traffic = None
    total_traffic = None
    enlarge_scale = None
    ehco_listen_host = None
    ehco_listen_port = None
    enable_ehco_lb = None
    ehco_ss_lb_port = models.IntegerField(
        "ss负载均衡端口", help_text="ss负载均衡端口", null=True, blank=True
    )
    ehco_vmess_lb_port = models.IntegerField(
        "vmess负载均衡端口", help_text="vmess负载均衡端口", null=True, blank=True
    )
    ehco_trojan_lb_port = models.IntegerField(
        "trojan负载均衡端口", help_text="trojan负载均衡端口", null=True, blank=True
    )

    server = models.CharField("服务器地址", max_length=128)
    isp = models.CharField("ISP线路", max_length=64, choices=ISP_TYPES, default=BGP)

    class Meta:
        verbose_name_plural = "中转节点"


class TrojanNode(BaseAbstractNode):

    BASE_CONFIG = {
        "stats": {},
        "api": {"tag": "api", "services": ["HandlerService", "StatsService"]},
        "log": {"loglevel": "info"},
        "policy": {
            "system": {"statsInboundUplink": True, "statsInboundDownlink": True},
        },
        "inbounds": [],
        "outbounds": [{"protocol": "freedom", "settings": {}}],
        "routing": {
            "settings": {
                "rules": [
                    {"inboundTag": ["api"], "outboundTag": "api", "type": "field"}
                ]
            },
            "strategy": "rules",
        },
    }

    server = models.CharField("服务器地址", max_length=128)
    inbound_tag = models.CharField("标签", default="proxy", max_length=64)
    service_port = models.IntegerField("服务端端口", default=443)
    client_port = models.IntegerField("客户端端口", default=443)
    listen_host = models.CharField("本地监听地址", max_length=64, default="0.0.0.0")
    grpc_host = models.CharField("grpc地址", max_length=64, default="0.0.0.0")
    grpc_port = models.CharField("grpc端口", max_length=64, default="8080")
    network = models.CharField("连接方式", max_length=64, default="tcp")
    security = models.CharField("加密方式", max_length=64, default="tls")
    skip_cert_verify = models.BooleanField(
        "是否允许不安全连接(跳过tls验证)", default=False, db_index=False
    )
    alpn = models.CharField("alpn", max_length=64, default="http/1.1")
    certificate_file = models.CharField("crt地址", max_length=64, default="path/to/cert")
    key_file = models.CharField("key地址", max_length=64, default="path/to/cert")

    class Meta:
        verbose_name_plural = "Trojan节点"


class VmessNode(BaseAbstractNode):

    BASE_CONFIG = {
        "stats": {},
        "api": {"tag": "api", "services": ["HandlerService", "StatsService"]},
        "log": {"loglevel": "info"},
        "policy": {
            "system": {"statsInboundUplink": True, "statsInboundDownlink": True},
        },
        "inbounds": [],
        "outbounds": [{"protocol": "freedom", "settings": {}}],
        "routing": {
            "settings": {
                "rules": [
                    {"inboundTag": ["api"], "outboundTag": "api", "type": "field"}
                ]
            },
            "strategy": "rules",
        },
    }

    server = models.CharField("服务器地址", max_length=128)
    inbound_tag = models.CharField("标签", default="proxy", max_length=64)
    service_port = models.IntegerField("服务端端口", default=10086)
    client_port = models.IntegerField("客户端端口", default=10086)
    alter_id = models.IntegerField("额外ID数量", default=1)
    listen_host = models.CharField("本地监听地址", max_length=64, default="0.0.0.0")
    grpc_host = models.CharField("grpc地址", max_length=64, default="0.0.0.0")
    grpc_port = models.CharField("grpc端口", max_length=64, default="8080")
    ws_host = models.CharField("域名", max_length=64, blank=True, null=True)
    ws_path = models.CharField("ws_path", max_length=64, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Vmess节点"


class SSNode(BaseAbstractNode):
    KB = 1024
    MEGABIT = KB * 125

    server = models.CharField("服务器地址", help_text="支持逗号分隔传多个地址", max_length=128)
    method = models.CharField(
        "加密类型", default=settings.DEFAULT_METHOD, max_length=32, choices=c.METHOD_CHOICES
    )
    speed_limit = models.IntegerField("限速", default=0)
    port = models.IntegerField("单端口", help_text="单端口多用户端口", null=True, blank=True)

    class Meta:
        verbose_name_plural = "SS节点"


class BaseRelayRule(models.Model):

    relay_port = models.CharField("中转端口", max_length=64, blank=False, null=False)
    listen_type = models.CharField(
        "监听类型", max_length=64, choices=c.LISTEN_TYPES, default=c.LISTEN_RAW
    )
    transport_type = models.CharField(
        "传输类型", max_length=64, choices=c.TRANSPORT_TYPES, default=c.TRANSPORT_RAW
    )

    class Meta:
        abstract = True


class TrojanRelayRule(BaseRelayRule):

    trojan_node = models.ForeignKey(
        TrojanNode,
        on_delete=models.CASCADE,
        verbose_name="Trojan节点",
        related_name="relay_rules",
    )
    relay_node = models.ForeignKey(
        RelayNode,
        on_delete=models.SET_NULL,
        verbose_name="中转节点",
        blank=True,
        null=True,
        related_name="trojan_relay_rules",
    )

    class Meta:
        verbose_name_plural = "Trojan转发规则"


class VmessRelayRule(BaseRelayRule):

    vmess_node = models.ForeignKey(
        VmessNode,
        on_delete=models.CASCADE,
        verbose_name="Vmess节点",
        related_name="relay_rules",
    )
    relay_node = models.ForeignKey(
        RelayNode,
        on_delete=models.SET_NULL,
        verbose_name="中转节点",
        blank=True,
        null=True,
        related_name="vmess_relay_rules",
    )

    class Meta:
        verbose_name_plural = "Vmess转发规则"


class SSRelayRule(BaseRelayRule):

    ss_node = models.ForeignKey(
        SSNode,
        on_delete=models.CASCADE,
        verbose_name="SS节点",
        related_name="relay_rules",
    )
    relay_node = models.ForeignKey(
        RelayNode,
        on_delete=models.SET_NULL,
        verbose_name="中转节点",
        blank=True,
        null=True,
        related_name="ss_relay_rules",
    )

    class Meta:
        verbose_name_plural = "SS转发规则"


class UserTrafficLog(models.Model, UserPropertyMixin):
    NODE_TYPE_SS = "ss"
    NODE_TYPE_VMESS = "vmess"
    NODE_TYPE_TROJAN = "trojan"
    NODE_CHOICES = (
        (NODE_TYPE_SS, NODE_TYPE_SS),
        (NODE_TYPE_VMESS, NODE_TYPE_VMESS),
        (NODE_TYPE_TROJAN, NODE_TYPE_TROJAN),
    )
    NODE_MODEL_DICT = {
        NODE_TYPE_SS: SSNode,
        NODE_TYPE_VMESS: VmessNode,
        NODE_TYPE_TROJAN: TrojanNode,
    }

    user_id = models.IntegerField()
    node_type = models.CharField(
        "节点类型", default=NODE_TYPE_SS, choices=NODE_CHOICES, max_length=32
    )
    node_id = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    upload_traffic = models.BigIntegerField("上传流量", default=0)
    download_traffic = models.BigIntegerField("下载流量", default=0)

    class Meta:
        verbose_name_plural = "流量记录"
        ordering = ["-date"]
        index_together = ["user_id", "node_type", "node_id", "date"]


# END TODO del


class InviteCode(models.Model):
    """邀请码"""

    TYPE_PUBLIC = 1
    TYPE_PRIVATE = 0
    INVITE_CODE_TYPE = ((TYPE_PUBLIC, "公开"), (TYPE_PRIVATE, "不公开"))

    code = models.CharField(
        verbose_name="邀请码",
        primary_key=True,
        blank=True,
        max_length=40,
        default=get_long_random_string,
    )
    code_type = models.IntegerField(
        verbose_name="类型", choices=INVITE_CODE_TYPE, default=TYPE_PRIVATE
    )
    user_id = models.PositiveIntegerField(verbose_name="邀请人ID", default=1)
    used = models.BooleanField(verbose_name="是否使用", default=False)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    def __str__(self):
        return f"<{self.user_id}>-<{self.code}>"

    class Meta:
        verbose_name_plural = "邀请码"
        ordering = ("used", "-created_at")

    @classmethod
    def calc_num_by_user(cls, user):
        return user.invitecode_num - cls.list_not_used_by_user_id(user.pk).count()

    @classmethod
    def create_by_user(cls, user):
        num = cls.calc_num_by_user(user)
        if num > 0:
            models = [cls(code_type=0, user_id=user.pk) for _ in range(num)]
            cls.objects.bulk_create(models)
        return num

    @classmethod
    def list_by_code_type(cls, code_type, num=20):
        return cls.objects.filter(code_type=code_type, used=False)[:num]

    @classmethod
    def list_by_user_id(cls, user_id, num=10):
        return cls.objects.filter(user_id=user_id)[:num]

    @classmethod
    def list_not_used_by_user_id(cls, user_id):
        return cls.objects.filter(user_id=user_id, used=False)

    def consume(self):
        self.used = True
        self.save()


class RebateRecord(models.Model, UserPropertyMixin):
    """返利记录"""

    user_id = models.PositiveIntegerField(verbose_name="返利人ID", default=1)
    consumer_id = models.PositiveIntegerField(
        verbose_name="消费者ID", null=True, blank=True
    )
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        null=True,
        default=0,
        max_digits=10,
        blank=True,
    )
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    class Meta:
        verbose_name_plural = "返利记录"
        ordering = ("-created_at",)

    @classmethod
    def list_by_user_id_with_consumer_username(cls, user_id, num=10):
        logs = cls.objects.filter(user_id=user_id)[:num]
        user_ids = [log.consumer_id for log in logs]
        username_map = {u.id: u.username for u in User.objects.filter(id__in=user_ids)}
        for log in logs:
            setattr(log, "consumer_username", username_map.get(log.consumer_id, ""))
        return logs


class Donate(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="捐赠人")
    time = models.DateTimeField(
        "捐赠时间", editable=False, auto_now_add=True, db_index=True
    )
    money = models.DecimalField(
        verbose_name="捐赠金额",
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
        db_index=True,
    )

    def __str__(self):
        return "{}-{}".format(self.user, self.money)

    class Meta:
        verbose_name_plural = "捐赠记录"
        ordering = ("-time",)

    @classmethod
    def get_donate_money_by_date(cls, date=None):
        qs = cls.objects.filter()
        if date:
            qs = qs.filter(time__gte=date, time__lte=date.add(days=1))
        res = qs.aggregate(amount=models.Sum("money"))["amount"]
        return int(res) if res else 0

    @classmethod
    def get_donate_count_by_date(cls, date=None):
        if date:
            return cls.objects.filter(time__gte=date).count()
        return cls.objects.all().count()

    @classmethod
    def get_most_donated_user_by_count(cls, count):
        return (
            cls.objects.values("user__username")
            .annotate(amount=models.Sum("money"))
            .order_by("-amount")[:count]
        )


class MoneyCode(models.Model):
    """充值码"""

    user = models.CharField(verbose_name="用户名", max_length=128, blank=True, null=True)
    time = models.DateTimeField("捐赠时间", editable=False, auto_now_add=True)
    code = models.CharField(
        verbose_name="充值码",
        unique=True,
        blank=True,
        max_length=40,
        default=get_long_random_string,
    )
    number = models.DecimalField(
        verbose_name="捐赠金额",
        decimal_places=2,
        max_digits=10,
        default=10,
        null=True,
        blank=True,
    )
    isused = models.BooleanField(verbose_name="是否使用", default=False)

    def clean(self):
        # 保证充值码不会重复
        code_length = len(self.code or "")
        if 0 < code_length < 12:
            self.code = "{}{}".format(self.code, get_long_random_string())
        else:
            self.code = get_long_random_string()

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = "充值码"
        ordering = ("isused",)


class Goods(models.Model):
    """商品"""

    STATUS_TYPE = ((1, "上架"), (-1, "下架"))

    name = models.CharField(verbose_name="商品名字", max_length=128, default="待编辑")
    content = models.CharField(verbose_name="商品描述", max_length=256, default="待编辑")
    transfer = models.BigIntegerField(verbose_name="增加的流量", default=settings.GB)
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )
    level = models.PositiveIntegerField(
        verbose_name="设置等级",
        default=0,
        validators=[MaxValueValidator(9), MinValueValidator(0)],
    )
    days = models.PositiveIntegerField(
        verbose_name="设置等级时间(天)",
        default=1,
        validators=[MaxValueValidator(365), MinValueValidator(1)],
    )
    status = models.SmallIntegerField("商品状态", default=1, choices=STATUS_TYPE)
    order = models.PositiveSmallIntegerField("排序", default=1)

    class Meta:
        verbose_name_plural = "商品"
        ordering = ["order"]

    def __str__(self):
        return self.name

    @property
    def total_transfer(self):
        """增加的流量"""
        return traffic_format(self.transfer)

    def get_days(self):
        """返回增加的天数"""
        return "{}".format(self.days)

    @transaction.atomic
    def purchase_by_user(self, user):
        """购买商品 返回是否成功"""
        if user.balance < self.money:
            return False
        # 验证成功进行提权操作
        user.balance -= self.money
        now = get_current_datetime()
        days = pendulum.duration(days=self.days)
        if user.level == self.level and user.level_expire_time > now:
            user.level_expire_time += days
            user.total_traffic += self.transfer
        else:
            user.level_expire_time = now + days
            user.reset_traffic(self.transfer)
        user.level = self.level
        user.save()
        # 增加购买记录
        PurchaseHistory.add_log(
            good_name=self.name, username=user.username, money=self.money
        )
        inviter = User.get_or_none(user.inviter_id)
        if inviter and inviter != user:
            # 增加返利记录
            rebaterecord = RebateRecord(
                user_id=inviter.pk,
                consumer_id=user.pk,
                money=self.money * Decimal(settings.INVITE_PERCENT),
            )
            inviter.balance += rebaterecord.money
            inviter.save()
            rebaterecord.save()
        return True


class PurchaseHistory(models.Model):
    """购买记录"""

    good_name = models.CharField(verbose_name="商品名", max_length=128, db_index=True)
    user = models.CharField(verbose_name="购买者", max_length=128)
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("购买时间", editable=False, auto_now_add=True)

    def __str__(self):
        return self.user

    class Meta:
        verbose_name_plural = "购买记录"
        ordering = ("-created_at",)

    @classmethod
    def cost_statistics(cls, good_id, start, end):
        start = pendulum.parse(start, tz=timezone.get_current_datetimezone())
        end = pendulum.parse(end, tz=timezone.get_current_datetimezone())
        good = Goods.objects.filter(pk=good_id).first()
        if not good:
            print("商品不存在")
            return
        query = cls.objects.filter(good_name=good.name, created_at__range=[start, end])
        count = query.count()
        amount = count * good.money
        print(
            "{} ~ {} 时间内 商品: {} 共销售 {} 次 总金额 {} 元".format(
                start.date(), end.date(), good, count, amount
            )
        )

    @classmethod
    def get_all_purchase_user(cls):
        username_list = [
            u["user"]
            for u in cls.objects.values("user")
            .annotate(c=models.Count("user"))
            .order_by("-c")
        ]
        return User.objects.find(username__in=username_list)

    @classmethod
    def add_log(cls, good_name, username, money):
        cls.objects.create(good_name=good_name, user=username, money=money)


class Announcement(models.Model):
    """公告界面"""

    time = models.DateTimeField("时间", auto_now_add=True)
    body = models.TextField("主体")

    def __str__(self):
        return "日期:{}".format(str(self.time)[:9])

    def save(self, *args, **kwargs):
        md = markdown.Markdown(extensions=["markdown.extensions.extra"])
        self.body = md.convert(self.body)
        super(Announcement, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "系统公告"
        ordering = ("-time",)

    @classmethod
    def send_first_visit_msg(cls, request):
        anno = cls.objects.order_by("-time").first()
        if not anno or request.session.get("first_visit"):
            return
        request.session["first_visit"] = True
        messages.warning(request, anno.plain_text, extra_tags="最新通知！")

    @property
    def plain_text(self):
        # TODO 现在db里存的是md转换成的html，这里之后可能要优化。转换的逻辑移到前端去
        re_br = re.compile("<br\s*?/?>")  # 处理换行
        re_h = re.compile("</?\w+[^>]*>")  # HTML标签
        s = re_br.sub("", self.body)  # 去掉br
        s = re_h.sub("", s)  # 去掉HTML 标签
        blank_line = re.compile("\n+")  # 去掉多余的空行
        s = blank_line.sub("", s)
        return s


class Ticket(models.Model):
    """工单"""

    TICKET_CHOICE = ((1, "开启"), (-1, "关闭"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    time = models.DateTimeField(verbose_name="时间", editable=False, auto_now_add=True)
    title = models.CharField(verbose_name="标题", max_length=128)
    body = models.TextField(verbose_name="内容主体")
    status = models.SmallIntegerField(
        verbose_name="状态", choices=TICKET_CHOICE, default=1
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "工单"
        ordering = ("-time",)


class EmailSendLog(models.Model):
    """邮件发送记录"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    subject = models.CharField(max_length=128, db_index=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "邮件发送记录"

    @classmethod
    def send_mail_to_users(cls, users, subject, message):
        address = [user.email for user in users]
        if send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, address):
            logs = [cls(user=user, subject=subject, message=message) for user in users]
            cls.objects.bulk_create(logs)
            print(f"send email success user: address: {address}")
        else:
            raise Exception(f"Could not send mail {address} subject: {subject}")

    @classmethod
    def get_user_dict_by_subject(cls, subject):
        return {l.user: 1 for l in cls.objects.filter(subject=subject)}
