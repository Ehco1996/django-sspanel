from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MaxValueValidator, MinValueValidator
# 自己写的小脚本 用于生成邀请码
from .tools import get_long_random_string, get_short_random_string

METHOD_CHOICES = (
    ('aes-256-cfb', 'aes-256-cfb'),
    ('rc4-md5', 'rc4-md5'),
    ('salsa20', 'salsa20'),
    ('aes-128-ctr', 'aes-128-ctr'),
)
STATUS_CHOICES = (
    ('ok', '好用'),
    ('slow', '不好用'),
    ('fail', '坏了'),
)

PROTOCOL_CHOICES = (
    ('auth_sha1_v4', 'auth_sha1_v4'),
    ('auth_aes128_md5', 'auth_aes128_md5'),
    ('auth_aes128_sha1', 'auth_aes128_sha1'),
    ('auth_chain_a', 'auth_chain_a'),
    ('origin', 'origin'),
)


OBFS_CHOICES = (
    ('plain', 'plain'),
    ('http_simple', 'http_simple'),
    ('http_post', 'http_post'),
    ('tls1.2_ticket_auth', 'tls1.2_ticket_auth'),
)

# Create your models here.


class User(AbstractUser):
    '''SS账户模型'''

    balance = models.DecimalField(
        '余额',
        decimal_places=2,
        max_digits=10,
        default=0,
        editable=False,
        null=True,
        blank=True,
    )

    invitecode = models.CharField(
        '邀请码',
        max_length=40,
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

    def __str__(self):
        return self.username
    class Meta(AbstractUser.Meta):
        verbose_name = '用户'


class Node(models.Model):
    '''线路节点'''

    name = models.CharField('名字', max_length=32,)

    server = models.CharField('服务器IP', max_length=128,)

    method = models.CharField(
        '加密类型', default='aes-256-cfb', max_length=32, choices=METHOD_CHOICES,)

    protocol = models.CharField(
        '协议', default='origin', max_length=32, choices=PROTOCOL_CHOICES,)

    obfs = models.CharField(
        '混淆', default='plain', max_length=32, choices=OBFS_CHOICES,)

    info = models.CharField('节点说明', max_length=1024, blank=True, null=True,)

    status = models.CharField(
        '状态', max_length=32, default='ok', choices=STATUS_CHOICES,)

    node_id = models.IntegerField('节点id', unique=True,)

    level = models.PositiveIntegerField(
        '节点等级',
        default=0,
        validators=[
            MaxValueValidator(9),
            MinValueValidator(0),
        ]
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['node_id']
        verbose_name_plural = '节点'


class InviteCode(models.Model):
    '''邀请码'''

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

    def clean(self):
        # 保证邀请码不会重复
        code_length = len(self.code or '')
        if 0 < code_length < 16:
            self.code = '{}{}'.format(
                self.code,
                get_long_random_string()
            )
        else:
            self.code = None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        # 重写save方法，在包存前执行我们写的clean方法
        self.clean()
        return super(InviteCode, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = '邀请码'
        ordering = ('-time_created',)


class Aliveip(models.Model):
    '''节点在线ip'''

    node_id = models.ForeignKey(
        Node,
        related_name='alive_node_id',
        on_delete=models.CASCADE,
        blank=True, null=True
    )

    user_name = models.CharField(
        '用户名',
        max_length=50,
        blank=True, null=True)

    ip_address = models.GenericIPAddressField('在线ip')

    local = models.CharField(
        '归属地',
        max_length=128,
        blank=True, null=True
    )
    time = models.DateTimeField(
        '时间',
        editable=False,
        auto_now_add=True
    )

    def __str__(self):
        return self.ip_address

    class Meta:
        verbose_name_plural = '在线ip'
        ordering = ('-time',)


class Donate(models.Model):
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

    )

    transfer = models.BigIntegerField(
        '增加的流量',
        default=1024 * 1024 * 1024
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

    def __str__(self):
        return self.name

    def get_transfer_by_GB(self):
        '''增加的流量以GB的形式返回'''
        return '{}'.format(self.transfer / 1024 / 1024 / 1024)

    class Meta:
        verbose_name_plural = '商品'


class PurchaseHistory(models.Model):
    '''购买记录'''

    info = models.ForeignKey(Shop)

    user = models.CharField(
        '购买者',
        max_length=128,

    )

    purchtime=models.DateTimeField(
        '购买时间',
        editable=False,
        auto_now_add=True
    )
    
    def __str__(self):
        return self.user
    
    class Meta:
        verbose_name_plural = '购买记录'
    