from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MaxValueValidator, MinValueValidator
# 自己写的小脚本 用于生成邀请码
from .tools import get_long_random_string, get_short_random_string
from django.conf import settings

import markdown
import datetime
import base64
import time

from ssserver.models import METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES


STATUS_CHOICES = (
    ('好用', '好用'),
    ('维护', '维护'),
    ('坏了', '坏了'),
)

# Create your models here.


class User(AbstractUser):
    '''SS账户模型'''

    @classmethod
    def proUser(cls):
        '''付费用户数量'''
        return len(cls.objects.filter(level__gt=0))

    @classmethod
    def userNum(cls):
        '''返回用户总数'''
        return len(cls.objects.all())

    @classmethod
    def todayRegister(cls):
        '''返回今日注册的用户'''
        # 获取今天凌晨的时间
        today = datetime.datetime.combine(
            datetime.date.today(), datetime.time.min)
        return cls.objects.filter(date_joined__gt=today)

    balance = models.DecimalField(
        '余额',
        decimal_places=2,
        max_digits=10,
        default=0,
        editable=True,
        null=True,
        blank=True,
    )

    invitecode = models.CharField(
        '邀请码',
        max_length=40,
    )

    invitecode_num = models.PositiveIntegerField(
        '可生成的邀请码数量',
        default=settings.INVITE_NUM
    )

    invited_by = models.PositiveIntegerField(
        '邀请人id',
        default=1,
    )

    # 最高等级限制为9级，和节点等级绑定
    level = models.PositiveIntegerField(
        '用户等级',
        default=0,
        validators=[
            MaxValueValidator(9),
            MinValueValidator(0),
        ]
    )

    level_expire_time = models.DateTimeField(
        '等级有效期',
        default=timezone.now,
        help_text='等级有效期',
    )

    def __str__(self):
        return self.username

    def get_expire_time(self):
        '''返回等级到期时间'''
        return self.level_expire_time

    def get_sub_link(self):
        '''生成该用户的订阅地址'''
        # 订阅地址
        token = base64.b64encode(
            bytes(self.username, 'utf-8')).decode('ascii') + '&&' + base64.b64encode(bytes(self.password, 'utf-8')).decode('ascii')
        sub_link = settings.HOST + 'server/subscribe/' + token
        return sub_link

    class Meta(AbstractUser.Meta):
        verbose_name = '用户'


class Node(models.Model):
    '''线路节点'''

    node_id = models.IntegerField('节点id', unique=True,)

    name = models.CharField('名字', max_length=32,)

    server = models.CharField('服务器IP', max_length=128,)

    method = models.CharField(
        '加密类型', default=settings.DEFAULT_METHOD, max_length=32, choices=METHOD_CHOICES,)

    custom_method = models.SmallIntegerField(
        '自定义加密',
        choices=(
            (0, 0),
            (1, 1)),
        default=0,
    )
    traffic_rate = models.FloatField(
        '流量比例',
        default=1.0
    )

    protocol = models.CharField(
        '协议', default=settings.DEFAULT_PROTOCOL, max_length=32, choices=PROTOCOL_CHOICES,)

    obfs = models.CharField(
        '混淆', default=settings.DEFAULT_OBFS, max_length=32, choices=OBFS_CHOICES,)

    info = models.CharField('节点说明', max_length=1024, blank=True, null=True,)

    status = models.CharField(
        '状态', max_length=32, default='ok', choices=STATUS_CHOICES,)

    level = models.PositiveIntegerField(
        '节点等级',
        default=0,
        validators=[
            MaxValueValidator(9),
            MinValueValidator(0),
        ]
    )

    show = models.CharField(
        '是否显示',
        max_length=32,
        choices=(
            ('显示', '显示'),
            ('不显示', '不显示')),
        default='显示',
    )

    group = models.CharField('分组', max_length=32, default='1')

    def __str__(self):
        return self.name

    def get_ssr_link(self, ss_user):
        '''返回ssr链接'''
        ssr_password = base64.b64encode(
            bytes(ss_user.password, 'utf8')).decode('ascii')
        ssr_remarks = base64.b64encode(
            bytes(self.name, 'utf8')).decode('ascii')
        ssr_group = base64.b64encode(
            bytes(self.group, 'utf8')).decode('ascii')
        if self.custom_method == 1:
            ssr_code = '{}:{}:{}:{}:{}:{}/?remarks={}&group={}'.format(
                self.server, ss_user.port, ss_user.protocol, ss_user.method, ss_user.obfs, ssr_password, ssr_remarks, ssr_group)
        else:
            ssr_code = '{}:{}:{}:{}:{}:{}/?remarks={}&group={}'.format(
                self.server, ss_user.port, self.protocol, self.method, self.obfs, ssr_password, ssr_remarks, ssr_group)
        ssr_pass = base64.b64encode(bytes(ssr_code, 'utf8')).decode('ascii')
        ssr_link = 'ssr://{}'.format(ssr_pass)
        return ssr_link

    def get_ss_link(self, ss_user):
        '''返回ss链接'''
        if self.custom_method == 1:
            ss_code = '{}:{}@{}:{}'.format(
                ss_user.method, ss_user.password, self.server, ss_user.port)
        else:
            ss_code = '{}:{}@{}:{}'.format(
                self.method, ss_user.password, self.server, ss_user.port)
        ss_pass = base64.b64encode(bytes(ss_code, 'utf8')).decode('ascii')
        ss_link = 'ss://{}'.format(ss_pass)
        return ss_link

    class Meta:
        ordering = ['id']
        verbose_name_plural = '节点'
        db_table = 'ss_node'


class NodeInfoLog(models.Model):
    '''节点负载记录'''

    node_id = models.IntegerField('节点id', blank=False, null=False)

    uptime = models.FloatField('更新时间', blank=False, null=False)

    load = models.CharField('负载', max_length=32, blank=False, null=False)

    log_time = models.IntegerField('日志时间', blank=False, null=False)

    def __str__(self):
        return str(self.node_id)

    class Meta:
        verbose_name_plural = '节点日志'
        db_table = 'ss_node_info_log'
        ordering = ('-log_time',)


class NodeOnlineLog(models.Model):
    '''节点在线记录'''

    @classmethod
    def totalOnlineUser(cls):
        '''返回所有节点的在线人数总和'''
        return sum([o.get_online_user() for o in cls.objects.all()])

    node_id = models.IntegerField('节点id', blank=False, null=False)

    online_user = models.IntegerField('在线人数', blank=False, null=False)

    log_time = models.IntegerField('日志时间', blank=False, null=False)

    def __str__(self):
        return '节点：{}'.format(self.node_id)

    def get_oneline_status(self):
        '''检测是否在线'''
        if int(time.time()) - self.log_time > 75:
            return False
        else:
            return True

    def get_online_user(self):
        '''返回在线人数'''
        if self.get_oneline_status() == True:
            return self.online_user
        else:
            return 0

    class Meta:
        verbose_name_plural = '节点在线记录'
        db_table = 'ss_node_online_log'


class InviteCode(models.Model):
    '''邀请码'''

    type = models.IntegerField(
        '类型',
        choices=((1, '公开'), (0, '不公开')),
        default=0,
    )

    code_id = models.PositiveIntegerField(
        '邀请人ID',
        default=1,
    )

    code = models.CharField(
        '邀请码',
        primary_key=True,
        blank=True,
        max_length=40,
        default=get_long_random_string
    )

    time_created = models.DateTimeField(
        '创建时间',
        editable=False,
        auto_now_add=True
    )

    isused = models.BooleanField(
        '是否使用',
        default=False,
    )

    def __str__(self):
        return str(self.code)

    class Meta:
        verbose_name_plural = '邀请码'
        ordering = ('isused', '-time_created',)


class RebateRecord(models.Model):
    '''返利记录'''

    user_id = models.PositiveIntegerField(
        '返利人ID',
        default=1,
    )

    money = models.DecimalField(
        '金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    rebatetime = models.DateTimeField(
        '返利时间',
        editable=False,
        auto_now_add=True
    )

    class Meta:
        ordering = ('-rebatetime',)


class Donate(models.Model):

    @classmethod
    def totalDonateMoney(cls):
        '''返回捐赠总金额'''
        return sum([d.money for d in cls.objects.all()])

    @classmethod
    def totalDonateNums(cls):
        '''返回捐赠总数量'''
        return len(cls.objects.all())

    @classmethod
    def richPeople(cls):
        '''返回捐赠金额最多的前10名'''
        rec = {}
        for d in cls.objects.all():
            if d.user not in rec.keys():
                rec[d.user] = d.money
            else:
                rec[d.user] += d.money
        return sorted(rec.items(), key=lambda rec: rec[1], reverse=True)[:10]

    '''捐赠记录'''
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    time = models.DateTimeField(
        '捐赠时间',
        editable=False,
        auto_now_add=True
    )

    money = models.DecimalField(
        '捐赠金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.money)

    class Meta:
        verbose_name_plural = '捐赠'
        ordering = ('-time',)


class MoneyCode(models.Model):
    '''充值码'''
    user = models.CharField(
        '用户名',
        max_length=128,
        blank=True,
        null=True,
    )

    time = models.DateTimeField(
        '捐赠时间',
        editable=False,
        auto_now_add=True
    )

    code = models.CharField(
        '充值码',
        unique=True,
        blank=True,
        max_length=40,
        default=get_long_random_string
    )

    number = models.DecimalField(
        '捐赠金额',
        decimal_places=2,
        max_digits=10,
        default=10,
        null=True,
        blank=True,
    )

    isused = models.BooleanField(
        '是否使用',
        default=False,
    )

    def clean(self):
        # 保证充值码不会重复
        code_length = len(self.code or '')
        if 0 < code_length < 12:
            self.code = '{}{}'.format(
                self.code,
                get_long_random_string()
            )
        else:
            self.code = get_long_random_string()

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = '充值码'
        ordering = ('isused',)


class Shop(models.Model):
    '''商品'''

    name = models.CharField(
        '商品描述',
        max_length=128,
        default='待编辑'
    )

    transfer = models.BigIntegerField(
        '增加的流量(GB)',
        default=1
    )

    money = models.DecimalField(
        '金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    level = models.PositiveIntegerField(
        '设置等级',
        default=0,
        validators=[
            MaxValueValidator(9),
            MinValueValidator(0),
        ]
    )

    days = models.PositiveIntegerField(
        '设置等级时间(天)',
        default=1,
        validators=[
            MaxValueValidator(365),
            MinValueValidator(1),
        ]
    )

    def __str__(self):
        return self.name

    def get_transfer_by_GB(self):
        '''增加的流量以GB的形式返回'''
        return '{}'.format(self.transfer / settings.GB)

    def get_days(self):
        '''返回增加的天数'''
        return '{}'.format(self.days)

    class Meta:
        verbose_name_plural = '商品'


class PurchaseHistory(models.Model):
    '''购买记录'''

    info = models.ForeignKey(Shop, on_delete=models.CASCADE)

    user = models.CharField(
        '购买者',
        max_length=128,

    )
    money = models.DecimalField(
        '金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    purchtime = models.DateTimeField(
        '购买时间',
        editable=False,
        auto_now_add=True
    )

    def __str__(self):
        return self.user

    class Meta:
        verbose_name_plural = '购买记录'
        ordering = ('-purchtime',)


class AlipayRecord(models.Model):
    '''充值流水单号记录'''

    username = models.CharField(
        '用户名',
        max_length=64,
        blank=False,
        null=False
    )

    info_code = models.CharField(
        '流水号',
        max_length=64,
        unique=True,
    )

    time = models.DateTimeField(
        '时间',
        auto_now_add=True
    )

    amount = models.DecimalField(
        '金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    money_code = models.CharField(
        '充值码',
        max_length=64,
        unique=True,
    )

    def __str__(self):
        return self.info_code

    class Meta:
        verbose_name_plural = '支付宝转账记录'
        ordering = ('-time',)


class AlipayRequest(models.Model):
    '''支付宝申请记录'''

    username = models.CharField(
        '用户名',
        max_length=64,
        blank=False,
        null=False
    )

    info_code = models.CharField(
        '流水号',
        max_length=64,
        unique=True,
    )

    time = models.DateTimeField(
        '时间',
        auto_now_add=True
    )

    amount = models.DecimalField(
        '金额',
        decimal_places=2,
        max_digits=10,
        default=0,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name_plural = '支付宝申请记录'
        ordering = ('-time',)


class Announcement(models.Model):
    '''公告界面'''
    time = models.DateTimeField(
        '时间',
        auto_now_add=True
    )

    body = models.TextField(
        '主体'
    )

    def __str__(self):
        return '日期:{}'.format(str(self.time)[:9])

    # 重写save函数，将文本渲染成markdown格式存入数据库
    def save(self, *args, **kwargs):
        # 首先实例化一个MarkDown类，来渲染一下body的文本 成为html文本
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
        ])
        self.body = md.convert(self.body)
        # 调动父类save 将数据保存到数据库中
        super(Announcement, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = '系统公告'
        ordering = ('-time',)


class Ticket(models.Model):
    '''工单'''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    time = models.DateTimeField(
        '时间',
        editable=False,
        auto_now_add=True
    )

    title = models.CharField(
        '标题',
        max_length=128,
    )

    body = models.TextField(
        '内容主体'
    )

    status = models.CharField(
        '状态',
        max_length=10,
        choices=(('开启', '开启'), ('关闭', '关闭')),
        default='开启',
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '工单'
        ordering = ('-time',)
