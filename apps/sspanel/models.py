import datetime
import time
from decimal import Decimal
from urllib.parse import urlencode

import markdown
import pendulum
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from apps.constants import THEME_CHOICES
from apps.payments import pay
from apps.utils import get_long_random_string, traffic_format


class User(AbstractUser):
    """SS账户模型"""

    SUB_TYPE_SS = 0
    SUB_TYPE_SSR = 1
    SUB_TYPE_ALL = 2

    SUB_TYPES = (
        (SUB_TYPE_SS, "只订阅SS"),
        (SUB_TYPE_SSR, "只订阅SSR"),
        (SUB_TYPE_ALL, "订阅所有"),
    )

    invitecode = models.CharField(verbose_name="邀请码", max_length=40)
    invited_by = models.PositiveIntegerField(verbose_name="邀请人id", default=1)
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
        verbose_name="用户等级",
        default=0,
        validators=[MaxValueValidator(9), MinValueValidator(0)],
    )
    level_expire_time = models.DateTimeField(verbose_name="等级有效期", default=timezone.now)
    theme = models.CharField(
        verbose_name="主题",
        choices=THEME_CHOICES,
        default=settings.DEFAULT_THEME,
        max_length=10,
    )
    sub_type = models.SmallIntegerField(
        verbose_name="订阅类型", choices=SUB_TYPES, default=SUB_TYPE_ALL
    )

    class Meta(AbstractUser.Meta):
        verbose_name = "用户"

    def delete(self):
        self.ss_user.delete()
        return super(User, self).delete()

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
    def add_new_user(cls, cleaned_data):
        from apps.ssserver.models import Suser

        with transaction.atomic():
            username = cleaned_data["username"]
            email = cleaned_data["email"]
            password = cleaned_data["password1"]
            invitecode = cleaned_data["invitecode"]
            user = cls.objects.create_user(username, email, password)
            code = InviteCode.objects.get(code=invitecode)
            code.isused = True
            code.save()
            # 将user和ssuser关联
            Suser.objects.create(user_id=user.id, port=Suser.get_random_port())
            # 绑定邀请人
            user.invited_by = code.code_id
            user.invitecode = invitecode
            user.save()
            Suser.clear_get_user_configs_by_node_id_cache()
            return user

    @classmethod
    def get_by_user_name(cls, username):
        return cls.objects.get(username=username)

    @classmethod
    def get_by_pk(cls, pk):
        return cls.objects.get(pk=pk)

    @classmethod
    def check_and_disable_expired_users(cls):
        now = pendulum.now()
        expired_user_emails = []
        for user in cls.objects.filter(level__gt=0, level_expire_time__lte=now):
            user.ss_user.reset_to_fresh()
            user.level = 0
            user.save()
            print(f"time: {now} user: {user} level timeout!")
            expired_user_emails.append(user.email)
        if expired_user_emails and settings.EXPIRE_EMAIL_NOTICE:
            send_mail(
                f"您的{settings.TITLE}账号已到期",
                f"您的账号现被暂停使用。如需继续使用请前往 {settings.HOST} 充值",
                settings.DEFAULT_FROM_EMAIL,
                expired_user_emails,
            )

    @property
    def sub_link(self):
        """生成该用户的订阅地址"""
        params = {"token": self.ss_user.token}
        return settings.HOST + f"/api/subscribe/?{urlencode(params)}"

    @property
    def ss_user(self):
        from apps.ssserver.models import Suser

        return Suser.objects.get(user_id=self.id)

    def get_sub_links(self):
        from apps.ssserver.models import Node

        if self.sub_type == User.SUB_TYPE_ALL:
            node_list = Node.objects.filter(level__lte=self.level, show=1)
        else:
            node_list = Node.objects.filter(
                level__lte=self.level, show=1, node_type=self.sub_type
            )

        ss_user = self.ss_user
        sub_links = "MAX={}\n".format(len(node_list))
        for node in node_list:
            sub_links = sub_links + node.get_node_link(ss_user) + "\n"
        return sub_links


class InviteCode(models.Model):
    """邀请码"""

    INVITE_CODE_TYPE = ((1, "公开"), (0, "不公开"))

    code_type = models.IntegerField(
        verbose_name="类型", choices=INVITE_CODE_TYPE, default=0
    )
    code_id = models.PositiveIntegerField(verbose_name="邀请人ID", default=1)
    code = models.CharField(
        verbose_name="邀请码",
        primary_key=True,
        blank=True,
        max_length=40,
        default=get_long_random_string,
    )
    time_created = models.DateTimeField(
        verbose_name="创建时间", editable=False, auto_now_add=True
    )
    isused = models.BooleanField(verbose_name="是否使用", default=False)

    def __str__(self):
        return str(self.code)

    class Meta:
        verbose_name_plural = "邀请码"
        ordering = ("isused", "-time_created")


class RebateRecord(models.Model):
    """返利记录"""

    user_id = models.PositiveIntegerField(verbose_name="返利人ID", default=1)
    rebatetime = models.DateTimeField(
        verbose_name="返利时间", editable=False, auto_now_add=True
    )
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        null=True,
        default=0,
        max_digits=10,
        blank=True,
    )

    class Meta:
        ordering = ("-rebatetime",)


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
        if date:
            return int(sum([d.money for d in cls.objects.filter(time__gte=date)]))
        return int(sum([d.money for d in cls.objects.all()]))

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

    def purchase_by_user(self, user):
        """购买商品 返回是否成功"""
        if user.balance < self.money:
            return False
        # 验证成功进行提权操作
        ss_user = user.ss_user
        user.balance -= self.money
        now = pendulum.now()
        days = pendulum.duration(days=self.days)
        if user.level == self.level and user.level_expire_time > now:
            user.level_expire_time += days
            ss_user.increase_transfer(self.transfer)
        else:
            user.level_expire_time = now + days
            ss_user.reset_traffic(self.transfer)
        ss_user.enable = True
        user.level = self.level
        ss_user.save()
        user.save()
        ss_user.clear_get_user_configs_by_node_id_cache()
        # 增加购买记录
        PurchaseHistory.objects.create(
            good=self, user=user, money=self.money, purchtime=now
        )
        # 增加返利记录
        inviter = User.objects.filter(pk=user.invited_by).first()
        if inviter:
            rebaterecord = RebateRecord(
                user_id=inviter.pk, money=self.money * Decimal(settings.INVITE_PERCENT)
            )
            inviter.balance += rebaterecord.money
            inviter.save()
            rebaterecord.save()
        return True


class PurchaseHistory(models.Model):
    """购买记录"""

    good = models.ForeignKey(Goods, on_delete=models.CASCADE, verbose_name="商品名")
    user = models.CharField(verbose_name="购买者", max_length=128)
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )
    purchtime = models.DateTimeField("购买时间", editable=False, auto_now_add=True)

    def __str__(self):
        return self.user

    class Meta:
        verbose_name_plural = "购买记录"
        ordering = ("-purchtime",)

    @classmethod
    def cost_statistics(cls, good_id, start, end):
        start = pendulum.parse(start, tz=timezone.get_current_timezone())
        end = pendulum.parse(end, tz=timezone.get_current_timezone())
        query = cls.objects.filter(
            good__id=good_id, purchtime__gte=start, purchtime__lte=end
        )
        for obj in query:
            print(obj.user, obj.good)
        count = query.count()
        amount = count * obj.money
        print(
            "{} ~ {} 时间内 商品: {} 共销售 {} 次 总金额 {} 元".format(
                start.date(), end.date(), obj.good, count, amount
            )
        )


class Announcement(models.Model):
    """公告界面"""

    time = models.DateTimeField("时间", auto_now_add=True)
    body = models.TextField("主体")

    def __str__(self):
        return "日期:{}".format(str(self.time)[:9])

    # 重写save函数，将文本渲染成markdown格式存入数据库
    def save(self, *args, **kwargs):
        # 首先实例化一个MarkDown类，来渲染一下body的文本 成为html文本
        md = markdown.Markdown(extensions=["markdown.extensions.extra"])
        self.body = md.convert(self.body)
        # 调动父类save 将数据保存到数据库中
        super(Announcement, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "系统公告"
        ordering = ("-time",)


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


class UserOrder(models.Model):

    DEFAULT_ORDER_TIME_OUT = "24h"
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
    qrcode_url = models.CharField(verbose_name="支付连接", max_length=64, null=True)
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
    def get_not_paid_order(cls, user, amount):
        return (
            cls.objects.filter(user=user, status=cls.STATUS_CREATED, amount=amount)
            .order_by("-created_at")
            .first()
        )

    @classmethod
    def get_recent_created_order(cls, user):
        return cls.objects.filter(user=user).order_by("-created_at").first()

    @classmethod
    def make_up_lost_orders(cls):
        now = pendulum.now()
        for order in cls.objects.filter(status=cls.STATUS_CREATED, expired_at__gte=now):
            changed = order.check_order_status()
            if changed:
                print(f"补单：{order.user,order.amount}")

    @classmethod
    def get_or_create_order(cls, user, amount):
        now = pendulum.now()
        order = cls.get_not_paid_order(user, amount)
        if order and order.expired_at > now:
            return order
        with transaction.atomic():
            out_trade_no = cls.gen_out_trade_no()
            trade = pay.alipay.api_alipay_trade_precreate(
                subject=settings.ALIPAY_TRADE_INFO.format(amount),
                out_trade_no=out_trade_no,
                total_amount=amount,
                timeout_express=cls.DEFAULT_ORDER_TIME_OUT,
                notify_url=settings.ALIPAY_CALLBACK_URL,
            )
            qrcode_url = trade.get("qr_code")
            order = cls.objects.create(
                user=user,
                status=cls.STATUS_CREATED,
                out_trade_no=out_trade_no,
                amount=amount,
                qrcode_url=qrcode_url,
                expired_at=now.add(hours=24),
            )
            return order

    def handle_paid(self):
        if self.status != self.STATUS_PAID:
            return
        with transaction.atomic():
            self.user.balance += self.amount
            self.user.save()
            self.status = self.STATUS_FINISHED
            self.save()
            # 将充值记录和捐赠绑定
            Donate.objects.create(user=self.user, money=self.amount)

    def check_order_status(self):
        changed = False
        if self.status != self.STATUS_CREATED:
            return
        with transaction.atomic():
            res = pay.alipay.api_alipay_trade_query(out_trade_no=self.out_trade_no)
            if res.get("trade_status", "") == "TRADE_SUCCESS":
                self.status = self.STATUS_PAID
                self.save()
                changed = True
        self.handle_paid()
        return changed
