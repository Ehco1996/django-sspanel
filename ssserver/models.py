# django自带功能模块
from django.db import models
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.shortcuts import resolve_url
from django.conf import settings

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
    ('aes-128-ctr', 'aes-128-ctr'),
    ('rc4-md5', 'rc4-md5'),
    ('salsa20', 'salsa20'),
    ('chacha20', 'chacha20'),
    ('none', 'none'),
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
    ('http_simple_compatible', 'http_simple_compatible'),
    ('http_post', 'http_post'),
    ('tls1.2_ticket_auth', 'tls1.2_ticket_auth'),
)

# Create your models here.


class SSUser(models.Model):

    @classmethod
    def userTodyChecked(cls):
        '''返回今日签到人数'''
        return len([o for o in cls.objects.all() if o.get_check_in()])

    @classmethod
    def userNeverChecked(cls):
        '''返回从未签到过人数'''
        return len([o for o in cls.objects.all() if o.last_check_in_time.year == 1970])

    @classmethod
    def userNeverUsed(cls):
        '''返回从未使用过的人数'''
        return len([o for o in cls.objects.all() if o.last_use_time == 0])

    @classmethod
    def coreUser(cls):
        '''返回流量用的最多的前十名用户'''
        rec = {}
        for u in cls.objects.filter(download_traffic__gt=0):
            rec[u] = u.upload_traffic + u.download_traffic
        # 按照流量倒序排序，切片取出前十名
        rec = sorted(rec.items(), key=lambda rec: rec[1], reverse=True)[:10]
        return [(r[0], r[0].get_traffic()) for r in rec]

    @classmethod
    def randomPord(cls):
        '''从其实端口~最大端口随机找出一个没有用过的端口'''
        users = cls.objects.all()
        port_list = []
        for user in users:
            '''将所有端口都加入列表'''
            port_list.append(int(user.port))
        # 生成从最小到最大的断口池
        all_ports = [i for i in range(1025, port_list[-1])]
        # 随机返回一个没有没占用的端口（取差集）
        return choice(list(set(all_ports).difference(set(port_list))))

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
        '加密类型', default=settings.DEFAULT_METHOD, max_length=32, choices=METHOD_CHOICES,)

    protocol = models.CharField(
        '协议', default=settings.DEFAULT_PROTOCOL, max_length=32, choices=PROTOCOL_CHOICES,)

    obfs = models.CharField(
        '混淆', default=settings.DEFAULT_OBFS, max_length=32, choices=OBFS_CHOICES,)

    def __str__(self):
        return self.user.username

    def get_last_use_time(self):
        '''返回上一次的使用到时间'''
        return timezone.datetime.fromtimestamp(self.last_use_time)

    def get_traffic(self):
        '''返回用户使用的总流量GB '''
        return '{:.2f}'.format((self.download_traffic + self.upload_traffic) / settings.GB)

    def get_transfer(self):
        '''返回用户的总流量 GB'''
        return '{:.2f} '.format(self.transfer_enable / settings.GB)

    def get_unused_traffic(self):
        '''返回用户的剩余流量'''
        return '{:.2f}'.format((self.transfer_enable - self.upload_traffic - self.download_traffic) / settings.GB)

    def get_used_percentage(self):
        '''返回用户的为使用流量百分比'''
        try:
            return '{:.2f}'.format((self.download_traffic + self.upload_traffic) / self.transfer_enable * 100)
        except ZeroDivisionError:
            return '100'

    def get_check_in(self):
        '''返回当天是否签到'''
        # 获取当天日期
        check_day = self.last_check_in_time.day
        now_day = datetime.datetime.now().day
        return check_day == now_day

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


class TrafficLog(models.Model):
    '''用户流量记录'''

    @classmethod
    def totalTraffic(cls, node_id):
        '''返回该节点使用总流量 单位GB'''
        traffics = cls.objects.filter(node_id=node_id)
        total_traffic = sum(
            [u.upload_traffic + u.download_traffic for u in traffics])
        return round(total_traffic / settings.GB, 2)

    @classmethod
    def getUserTraffic(cls, node_id, user_id):
        '''返回指定用户对应节点的流量 单位GB'''
        traffics = cls.objects.filter(node_id=node_id, user_id=user_id)
        total_traffic = sum(
            [u.upload_traffic + u.download_traffic for u in traffics])
        return round(total_traffic / settings.GB, 2)

    @classmethod
    def getTrafficByDay(cls, node_id, user_id, date):
        '''返回指定用户对应节点对应日期的流量 单位GB'''
        traffics = cls.objects.filter(
            node_id=node_id, user_id=user_id, log_date__year=date.year, log_date__month=date.month, log_date__day=date.day)
        total_traffic = sum(
            [u.upload_traffic + u.download_traffic for u in traffics])
        return round(total_traffic / settings.GB, 2)

    user_id = models.IntegerField('用户id', blank=False, null=False)
    node_id = models.IntegerField('节点id', blank=False, null=False)
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
    rate = models.FloatField('流量比例', default=1.0, null=False)
    traffic = models.CharField('流量记录', max_length=32, null=False)
    log_time = models.IntegerField('日志时间', blank=False, null=False)
    log_date = models.DateTimeField(
        '记录日期', default=timezone.now, blank=False, null=False)

    def __str__(self):
        return self.traffic

    class Meta:
        verbose_name_plural = '流量记录'
        ordering = ('-log_time',)
        db_table = 'user_traffic_log'
