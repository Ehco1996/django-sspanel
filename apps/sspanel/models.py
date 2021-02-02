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
from django.db import models, transaction
from django.utils import functional, timezone
from redis.exceptions import LockError

from apps import constants as c
from apps.ext import cache, encoder, lock, pay
from apps.utils import (
    get_current_datetime,
    get_long_random_string,
    get_short_random_string,
    traffic_format,
)


class User(AbstractUser):

    MIN_PORT = 1025
    PORT_BLACK_SET = {6443, 8472}

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

    class Meta(AbstractUser.Meta):
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.username

    @classmethod
    @cache.cached()
    def get_by_id_with_cache(cls, id):
        return cls.objects.get(id=id)

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

    @classmethod
    def get_new_user_count_by_datetime(cls, date: pendulum.DateTime):
        return cls.objects.filter(
            date_joined__range=[
                date.start_of("day"),
                date.end_of("day"),
            ]
        ).aggregate(count=models.Count("id"))["count"]

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
        self.ss_port = port
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


class UserMixin:
    @functional.cached_property
    def user(self):
        return User.get_by_pk(self.user_id)


class UserOrder(models.Model, UserMixin):

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
        verbose_name = "用户订单"
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

    @classmethod
    def get_success_order_count(cls, dt: pendulum.DateTime):
        return cls.objects.filter(
            created_at__range=[dt.start_of("day"), dt.end_of("day")],
            status=cls.STATUS_FINISHED,
        ).count()

    @classmethod
    def get_success_order_amount(cls, date: pendulum.DateTime):
        amount = (
            cls.objects.filter(
                status=cls.STATUS_FINISHED,
                created_at__range=[
                    date.start_of("day"),
                    date.end_of("day"),
                ],
            ).aggregate(amount=models.Sum("amount"))["amount"]
            or "0"
        )
        return amount

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


class UserRefLog(models.Model, UserMixin):
    user_id = models.PositiveIntegerField()
    register_count = models.IntegerField(default=0)
    date = models.DateField("记录日期", default=pendulum.today, db_index=True)

    class Meta:
        verbose_name = "用户推荐记录"
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
    def calc_user_total_ref_count(cls, user_id):
        aggs = cls.objects.filter(user_id=user_id).aggregate(
            register_count=models.Sum("register_count")
        )
        return aggs["register_count"] if aggs["register_count"] else 0


class UserCheckInLog(models.Model, UserMixin):
    user_id = models.PositiveIntegerField()
    date = models.DateField("记录日期", default=pendulum.today, db_index=True)
    increased_traffic = models.BigIntegerField("增加的流量", default=0)

    class Meta:
        verbose_name = "用户签到记录"
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
    def get_checkin_user_count(cls, date: pendulum.Date):
        return cls.objects.filter(date=date).count()

    @property
    def human_increased_traffic(self):
        return traffic_format(self.increased_traffic)


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
        verbose_name = "邀请码"
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


class RebateRecord(models.Model, UserMixin):
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
        verbose_name = "返利记录"
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
        verbose_name = "捐赠记录"
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

    class Meta:
        verbose_name = "充值码"
        verbose_name_plural = "充值码"
        ordering = ("isused",)

    def clean(self):
        # 保证充值码不会重复
        code_length = len(self.code or "")
        if 0 < code_length < 12:
            self.code = "{}{}".format(self.code, get_long_random_string())
        else:
            self.code = get_long_random_string()

    def __str__(self):
        return self.code


class Goods(models.Model):
    """商品"""

    STATUS_ON = 1
    STATUS_OFF = -1
    STATUS_TYPE = ((STATUS_ON, "上架"), (STATUS_OFF, "下架"))

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
    user_purchase_count = models.IntegerField(
        "每名用户可购买数量",
        default=0,
        help_text="0表示不限制",
    )

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ["order"]

    def __str__(self):
        return self.name

    @classmethod
    def get_user_can_buy_goods(cls, user: User):
        return [
            good
            for good in cls.objects.filter(status=cls.STATUS_ON)
            if good.user_can_buy(user)
        ]

    @property
    def total_transfer(self):
        """增加的流量"""
        return traffic_format(self.transfer)

    @property
    def status_cn(self):
        if self.status == self.STATUS_ON:
            return "上架"
        else:
            return "下架"

    @property
    def bulma_color(self):
        """bulma的颜色 虽然不该写在这里,但是前端太苦手了算啦"""
        if self.days <= 10:
            return "is-info"
        elif 10 < self.days <= 30:
            return "is-success"
        elif 30 < self.days <= 100:
            return "is-warning"
        return "is-danger is-active"

    def user_can_buy(self, user: User):
        return not (
            self.user_purchase_count > 0
            and PurchaseHistory.get_by_user_and_good(user, self).count()
            >= self.user_purchase_count
        )

    @transaction.atomic
    def purchase_by_user(self, user):
        """购买商品 返回是否成功"""
        if user.balance < self.money or not self.user_can_buy(user):
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
        user.save(
            update_fields=[
                "level",
                "balance",
                "total_traffic",
                "upload_traffic",
                "download_traffic",
                "level_expire_time",
            ]
        )
        # 增加购买记录
        PurchaseHistory.add_log(good=self, user=user)
        inviter = User.get_or_none(user.inviter_id)
        if inviter and inviter != user:
            # 增加返利记录
            rebaterecord = RebateRecord(
                user_id=inviter.pk,
                consumer_id=user.pk,
                money=self.money * Decimal(settings.INVITE_PERCENT),
            )
            inviter.balance += rebaterecord.money
            inviter.save(update_fields=["balance"])
            rebaterecord.save()
        return True


class PurchaseHistory(models.Model):
    """用户购买记录"""

    good_id = models.IntegerField("商品ID", default=12, db_index=True)
    user_id = models.IntegerField("用户ID", default=12, db_index=True)
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
        verbose_name = "用户购买记录"
        verbose_name_plural = "用户购买记录"
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
    def add_log(cls, good, user):
        cls.objects.create(
            good_name=good.name,
            good_id=good.id,
            user=user.username,
            user_id=user.id,
            money=good.money,
        )

    @classmethod
    def get_by_user_and_good(cls, user, good):
        return cls.objects.filter(user_id=user.id, good_id=good.id)


class Announcement(models.Model):
    """公告界面"""

    time = models.DateTimeField("时间", auto_now_add=True)
    body = models.TextField("主体")

    class Meta:
        verbose_name = "系统公告"
        verbose_name_plural = "系统公告"
        ordering = ("-time",)

    def __str__(self):
        return "日期:{}".format(str(self.time)[:9])

    def save(self, *args, **kwargs):
        md = markdown.Markdown(extensions=["markdown.extensions.extra"])
        self.body = md.convert(self.body)
        super(Announcement, self).save(*args, **kwargs)

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
        verbose_name = "工单"
        verbose_name_plural = "工单"
        ordering = ("-time",)


class EmailSendLog(models.Model):
    """邮件发送记录"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    subject = models.CharField(max_length=128, db_index=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "邮件发送记录"
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


class UserSubLog(models.Model):
    SUB_TYPES = (
        ("ss", "订阅SS"),
        ("vless", "订阅Vless"),
        ("trojan", "订阅Trojan"),
        ("clash", "订阅Clash"),
        ("clash_pro", "订阅ClashPro"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    sub_type = models.CharField("订阅类型", choices=SUB_TYPES, max_length=20)
    ip = models.CharField(max_length=128, verbose_name="IP地址")
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="创建时间", verbose_name="创建时间"
    )

    class Meta:
        verbose_name = "用户订阅记录"
        verbose_name_plural = "用户订阅记录"
        ordering = ["-created_at"]
        index_together = ["user", "created_at"]

    @classmethod
    def add_log(cls, user, sub_type, ip):
        return cls.objects.create(user=user, sub_type=sub_type, ip=ip)
