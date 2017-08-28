# django自带功能模块
from django.db import models
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.shortcuts import resolve_url

# python标准库
import datetime
from random import choice

# 自己编写的脚本
from shadowsocks.tools import get_short_random_string


PLAN_CHOICES = (
    ('free', 'Free'),
    ('pro', 'pro')
)
METHOD_CHOICES = (
    ('aes-256-cfb', 'aes-256-cfb'),
    ('rc4-md5', 'rc4-md5'),
    ('salsa20', 'salsa20'),
    ('aes-128-ctr', 'aes-128-ctr'),
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


class SSUser(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ss_user'
    )

    plan = models.CharField(
        '套餐',
        max_length=32,
        default='Free',
        choices=PLAN_CHOICES,
    )

    last_check_in_time = models.DateTimeField(
        '最后签到时间',
        null=True,
        # 默认设置为时间戳开始的那天
        default=datetime.datetime.fromtimestamp(0),
        editable=False,
    )

    # shadowsocks 数据库表字段
    password = models.CharField(
        'Shadowsocks密码',
        max_length=32,
        # 当密码少于6位时报错
        validators=[validators.MinLengthValidator(6), ],
        default=get_short_random_string,
        db_column='passwd',
    )
    port = models.IntegerField(
        '端口',
        db_column='port',
        unique=True,
    )
    last_use_time = models.IntegerField(
        '最后使用时间',
        default=0,
        editable=False,
        help_text='时间戳',
        db_column='t'
    )
    upload_traffic = models.BigIntegerField(
        '上传流量',
        default=0,
        db_column='u'
    )
    download_traffic = models.BigIntegerField(
        '下载流量',
        default=0,
        db_column='d'
    )
    transfer_enable = models.BigIntegerField(
        '总流量',
        default=settings.DEFAULT_TRAFFIC,
        db_column='transfer_enable'
    )
    switch = models.BooleanField(
        '保留字段switch',
        default=True,
        db_column='switch',
    )
    enable = models.BooleanField(
        '开启与否',
        default=True,
        db_column='enable',
    )

    method = models.CharField(
        '加密类型', default='aes-256-cfb', max_length=32, choices=METHOD_CHOICES,)

    protocol = models.CharField(
        '协议', default='origin', max_length=32, choices=PROTOCOL_CHOICES,)

    obfs = models.CharField(
        '混淆', default='plain', max_length=32, choices=OBFS_CHOICES,)

    def __str__(self):
        return self.user.username

    def get_last_use_time(self):
        '''返回上一次的使用到时间'''
        return timezone.datetime.fromtimestamp(self.last_use_time)

    def get_traffic(self):
        '''返回用户使用的总流量mb '''
        return '{:.2f}'.format((self.download_traffic + self.upload_traffic) / 1024 / 1024)

    def get_transfer(self):
        '''返回用户的总流量 GB'''
        return '{:.2f} '.format(self.transfer_enable / 1024 / 1024 / 1024)

    def get_unused_traffic(self):
        '''返回用户的剩余流量'''
        return '{:.2f}'.format((self.enable - self.upload_traffic - self.download_traffic) / 1024 / 1024)

    def get_used_percentage(self):
        '''返回用户的为使用流量百分比'''
        return '{:.2f}'.format((self.download_traffic + self.upload_traffic) / self.transfer_enable * 100)

    def get_check_in(self):
        '''返回当天是否签到'''
        return timezone.now() - datetime.timedelta(days=1) < self.last_check_in_time

    @classmethod
    def get_absolute_url(cls):
        '''返回url链接'''
        return resolve_url('shadowsocks:index')

    def clean(self):
        '''保证端口在1024<50000之间'''
        if self.port:
            if not 1024 < self.port < 50000:
                raise ValidationError('端口必须在1024和50000之间')
        else:
            max_port_user = SSUser.objects.order_by('-port').first()
            if max_port_user:
                self.port = max_port_user.port + choice([2, 3])
            else:
                self.port = settings.START_PORT

    class Meta:
        verbose_name_plural = 'SS账户'
        ordering = ('-last_check_in_time',)
        db_table = 'user'
