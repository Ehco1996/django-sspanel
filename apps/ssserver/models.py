import time
import base64
from random import choice

import pendulum
from django_prometheus.models import ExportModelOperationsMixin
from django.db.models import F
from django.conf import settings
from django.utils import timezone
from django.core import validators
from django.db import models, connection
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from apps.utils import (get_short_random_string,
                        traffic_format, get_current_time)
from apps.constants import (METHOD_CHOICES, PROTOCOL_CHOICES, OBFS_CHOICES,
                            COUNTRIES_CHOICES, NODE_TIME_OUT)


class Suser(ExportModelOperationsMixin('ss_user'), models.Model):
    '''与user通过user_id作为虚拟外键关联'''

    user_id = models.IntegerField(
        verbose_name='user_id', db_column='user_id', unique=True, db_index=True)
    last_check_in_time = models.DateTimeField(
        verbose_name='最后签到时间', null=True, editable=False)
    password = models.CharField(verbose_name='ss密码', max_length=32, default=get_short_random_string,
                                db_column='passwd', validators=[validators.MinLengthValidator(6), ])
    port = models.IntegerField(
        verbose_name='端口', db_column='port', unique=True,)
    last_use_time = models.IntegerField(
        verbose_name='最后使用时间', default=0, editable=False, help_text='时间戳', db_column='t')
    upload_traffic = models.BigIntegerField(
        verbose_name='上传流量', default=0, db_column='u')
    download_traffic = models.BigIntegerField(
        verbose_name='下载流量', default=0, db_column='d')
    transfer_enable = models.BigIntegerField(
        verbose_name='总流量', default=settings.DEFAULT_TRAFFIC, db_column='transfer_enable')
    switch = models.BooleanField(
        verbose_name='保留字段switch', default=True, db_column='switch')
    enable = models.BooleanField(
        verbose_name='开启与否', default=True, db_column='enable')
    method = models.CharField(
        verbose_name='加密类型', default=settings.DEFAULT_METHOD, max_length=32, choices=METHOD_CHOICES,)
    protocol = models.CharField(
        verbose_name='协议', default=settings.DEFAULT_PROTOCOL, max_length=32, choices=PROTOCOL_CHOICES)
    protocol_param = models.CharField(
        verbose_name='协议参数', max_length=128, null=True, blank=True)
    obfs = models.CharField(
        verbose_name='混淆', default=settings.DEFAULT_OBFS, max_length=32, choices=OBFS_CHOICES)
    obfs_param = models.CharField(
        verbose_name='混淆参数', max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Ss用户'
        ordering = ('-last_check_in_time', )
        db_table = 's_user'

    def __str__(self):
        return self.user.username

    def clean(self):
        '''保证端口在1024<50000之间'''
        if self.port:
            if not 1024 < self.port < 50000:
                raise ValidationError('端口必须在1024和50000之间')

    @property
    def user(self):
        from apps.sspanel.models import User
        return User.objects.get(pk=self.user_id)

    @property
    def today_is_checked(self):
        if self.last_check_in_time:
            return self.last_check_in_time.day == timezone.now().day
        return False

    @property
    def user_last_use_time(self):
        t = pendulum.from_timestamp(self.last_use_time, tz=settings.TIME_ZONE)
        return t

    @property
    def used_traffic(self):
        return traffic_format(self.download_traffic + self.upload_traffic)

    @property
    def totla_transfer(self):
        return traffic_format(self.transfer_enable)

    @property
    def unused_traffic(self):
        return traffic_format(
            self.transfer_enable - self.upload_traffic - self.download_traffic)

    @property
    def used_percentage(self):
        try:
            used = self.download_traffic + self.upload_traffic
            return used / self.transfer_enable * 100
        except ZeroDivisionError:
            return 100

    @classmethod
    def get_today_checked_user_num(cls):
        now = get_current_time()
        midnight = pendulum.datetime(
            year=now.year, month=now.month, day=now.day, tz=now.tz)
        query = cls.objects.filter(last_check_in_time__gte=midnight)
        return query.count()

    @classmethod
    def get_never_checked_user_num(cls):
        return cls.objects.filter(last_check_in_time=None).count()

    @classmethod
    def get_never_used_num(cls):
        '''返回从未使用过的人数'''
        return cls.objects.filter(last_use_time=0).count()

    @classmethod
    def get_user_by_traffic(cls, num=10):
        '''返回流量用的最多的前num名用户'''
        return cls.objects.all().order_by('-download_traffic')[:10]

    @classmethod
    def get_vaild_user(cls, level):
        '''返回指大于等于指定等级的所有合法用户'''
        from apps.sspanel.models import User
        user_ids = User.objects.filter(level__gte=level).values_list('id')
        users = cls.objects.filter(transfer_enable__gte=(
            F('upload_traffic') + F('download_traffic')), user_id__in=user_ids)
        return users

    @classmethod
    def get_random_port(cls):
        users = cls.objects.all().values_list('port')
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


class Node(ExportModelOperationsMixin('node'), models.Model):
    '''线路节点'''
    SHOW_CHOICES = ((1, '显示'), (-1, '不显示'))

    NODE_TYPE_CHOICES = ((0, '多端口多用户'), (1, '单端口多用户'))

    CUSTOM_METHOD_CHOICES = ((0, '否'), (1, '是'))

    SS_TYPE_CHOICES = ((0, 'SS'), (1, 'SSR'), (2, 'SS/SSR'))

    @classmethod
    def get_import_code(cls, user):
        '''获取该用户的所有节点的导入信息'''
        ss_user = user.ss_user
        sub_code_list = []
        node_list = cls.objects.filter(level__lte=user.level, show=1)
        for node in node_list:
            sub_code_list.append(node.get_node_link(ss_user))
        return '\n'.join(sub_code_list)

    @classmethod
    def get_node_ids(cls, all=False):
        '''返回所有节点的id'''
        if all is False:
            nodes = cls.objects.filter(show=1)
        else:
            nodes = cls.objects.all()
        return [node.node_id for node in nodes]

    node_id = models.IntegerField('节点id', unique=True)
    port = models.IntegerField(
        '节点端口', default=443, blank=True, help_text='单端口多用户时需要')
    password = models.CharField(
        '节点密码', max_length=32, default='password', help_text='单端口时需要')
    country = models.CharField(
        '国家', default='CN', max_length=2, choices=COUNTRIES_CHOICES)
    custom_method = models.SmallIntegerField(
        '自定义加密', choices=CUSTOM_METHOD_CHOICES, default=0)
    show = models.SmallIntegerField('是否显示', choices=SHOW_CHOICES, default=1)
    node_type = models.SmallIntegerField(
        '节点类型', choices=NODE_TYPE_CHOICES, default=0)
    ss_type = models.SmallIntegerField(
        'SS类型', choices=SS_TYPE_CHOICES, default=2)
    name = models.CharField('名字', max_length=32)
    info = models.CharField('节点说明', max_length=1024, blank=True, null=True)
    server = models.CharField('服务器IP', max_length=128)
    method = models.CharField('加密类型', default=settings.DEFAULT_METHOD,
                              max_length=32, choices=METHOD_CHOICES,)
    traffic_rate = models.FloatField('流量比例', default=1.0)
    protocol = models.CharField('协议', default=settings.DEFAULT_PROTOCOL,
                                max_length=32, choices=PROTOCOL_CHOICES,)
    protocol_param = models.CharField(
        '协议参数', max_length=128, default="", blank=True)
    obfs = models.CharField('混淆', default=settings.DEFAULT_OBFS,
                            max_length=32, choices=OBFS_CHOICES,)
    obfs_param = models.CharField(
        '混淆参数', max_length=255, default="", blank=True)
    level = models.PositiveIntegerField(
        '节点等级', default=0,
        validators=[MaxValueValidator(9), MinValueValidator(0)])
    total_traffic = models.BigIntegerField('总流量', default=settings.GB)
    used_traffic = models.BigIntegerField('已用流量', default=0,)
    order = models.PositiveSmallIntegerField('排序', default=1)
    group = models.CharField('分组名', max_length=32, default='谜之屋')

    def __str__(self):
        return self.name

    def get_ssr_link(self, ss_user):
        '''返回ssr链接'''
        ssr_password = base64.urlsafe_b64encode(
            bytes(ss_user.password, 'utf8')).decode('utf8')
        ssr_remarks = base64.urlsafe_b64encode(bytes(self.name,
                                                     'utf8')).decode('utf8')
        ssr_group = base64.urlsafe_b64encode(bytes(self.group,
                                                   'utf8')).decode('utf8')
        if self.node_type == 1:
            # 单端口多用户
            ssr_password = base64.urlsafe_b64encode(
                bytes(self.password, 'utf8')).decode('utf8')
            info = '{}:{}'.format(ss_user.port, ss_user.password)
            protocol_param = base64.urlsafe_b64encode(bytes(
                info, 'utf8')).decode('utf8')
            obfs_param = base64.urlsafe_b64encode(
                bytes(str(self.obfs_param), 'utf8')).decode('utf8')
            ssr_code = '{}:{}:{}:{}:{}:{}/?obfsparam={}&protoparam={}&remarks={}&group={}'.format(
                self.server, self.port, self.protocol, self.method, self.obfs,
                ssr_password, obfs_param, protocol_param, ssr_remarks,
                ssr_group)
        elif self.custom_method == 1:
            ssr_code = '{}:{}:{}:{}:{}:{}/?remarks={}&group={}'.format(
                self.server, ss_user.port, ss_user.protocol, ss_user.method,
                ss_user.obfs, ssr_password, ssr_remarks, ssr_group)
        else:
            ssr_code = '{}:{}:{}:{}:{}:{}/?remarks={}&group={}'.format(
                self.server, ss_user.port, self.protocol, self.method,
                self.obfs, ssr_password, ssr_remarks, ssr_group)
        ssr_pass = base64.urlsafe_b64encode(bytes(ssr_code,
                                                  'utf8')).decode('utf8')
        ssr_link = 'ssr://{}'.format(ssr_pass)
        return ssr_link

    def get_ss_link(self, ss_user):
        '''返回ss链接'''
        if self.custom_method == 1:
            ss_code = '{}:{}@{}:{}'.format(ss_user.method, ss_user.password,
                                           self.server, ss_user.port)
        else:
            ss_code = '{}:{}@{}:{}'.format(self.method, ss_user.password,
                                           self.server, ss_user.port)
        ss_pass = base64.urlsafe_b64encode(bytes(ss_code,
                                                 'utf8')).decode('utf8')
        ss_link = 'ss://{}#{}'.format(ss_pass, self.name)
        return ss_link

    def get_node_link(self, ss_user):
        '''获取当前的节点链接'''
        if self.ss_type == 0:
            return self.get_ss_link(ss_user)
        else:
            return self.get_ssr_link(ss_user)

    def save(self, *args, **kwargs):
        if self.node_type == 1:
            self.custom_method = 0
        super(Node, self).save(*args, **kwargs)

    def human_total_traffic(self):
        '''总流量'''
        return traffic_format(self.total_traffic)

    def human_used_traffic(self):
        '''已用流量'''
        return traffic_format(self.used_traffic)

    @classmethod
    def get_by_node_id(cls, node_id):
        return cls.objects.get(node_id=node_id)
    # verbose_name
    human_total_traffic.short_description = '总流量'
    human_used_traffic.short_description = '使用流量'

    class Meta:
        ordering = ['-show', 'order']
        verbose_name_plural = '节点'
        db_table = 'ss_node'


class TrafficLog(ExportModelOperationsMixin('traffic_log'), models.Model):
    '''用户流量记录'''

    user_id = models.IntegerField(
        '用户id', blank=False, null=False, db_index=True)
    node_id = models.IntegerField(
        '节点id', blank=False, null=False, db_index=True)
    upload_traffic = models.BigIntegerField('上传流量', default=0, db_column='u')
    download_traffic = models.BigIntegerField('下载流量', default=0, db_column='d')
    rate = models.FloatField('流量比例', default=1.0, null=False)
    traffic = models.CharField('流量记录', max_length=32, null=False)
    log_time = models.IntegerField('日志时间', blank=False, null=False)
    log_date = models.DateField(
        '记录日期', default=timezone.now, blank=False, null=False, db_index=True)

    def __str__(self):
        return self.traffic

    class Meta:
        verbose_name_plural = '流量记录'
        ordering = ('-log_time', )
        db_table = 'user_traffic_log'

    @property
    def user(self):
        from apps.sspanel.models import User
        return User.objects.get(pk=self.user_id)

    @property
    def used_traffic(self):
        return self.download_traffic + self.upload_traffic

    @classmethod
    def get_user_traffic(cls, node_id, user_id):
        logs = cls.objects.filter(node_id=node_id, user_id=user_id)
        return traffic_format(sum([l.used_traffic for l in logs]))

    @classmethod
    def get_traffic_by_date(cls, node_id, user_id, date):
        logs = cls.objects.filter(node_id=node_id, user_id=user_id,
                                  log_date=date)
        return round(sum([l.used_traffic for l in logs]) / settings.MB, 1)

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute(
                'TRUNCATE TABLE {}'.format(cls._meta.db_table))


class NodeOnlineLog(ExportModelOperationsMixin('node_onlie_log'), models.Model):
    '''节点在线记录'''

    @classmethod
    def totalOnlineUser(cls):
        '''返回所有节点的在线人数总和'''
        count = 0
        node_ids = [
            o['node_id'] for o in Node.objects.filter(show=1).values('node_id')
        ]
        for node_id in node_ids:
            o = cls.objects.filter(node_id=node_id).order_by('-log_time')[:1]
            if o:
                count += o[0].get_online_user()
        return count

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute(
                'TRUNCATE TABLE {}'.format(cls._meta.db_table))

    node_id = models.IntegerField('节点id', blank=False, null=False)
    online_user = models.IntegerField('在线人数', blank=False, null=False)
    log_time = models.IntegerField('日志时间', blank=False, null=False)

    def __str__(self):
        return '节点：{}'.format(self.node_id)

    def get_oneline_status(self):
        '''检测是否在线'''
        if int(time.time()) - self.log_time > NODE_TIME_OUT:
            return False
        else:
            return True

    def get_online_user(self):
        '''返回在线人数'''
        if self.get_oneline_status() is True:
            return self.online_user
        else:
            return 0

    class Meta:
        verbose_name_plural = '节点在线记录'
        db_table = 'ss_node_online_log'


class AliveIp(ExportModelOperationsMixin('aliveip_log'), models.Model):
    @classmethod
    def recent_alive(cls, node_id):
        '''
        返回节点最近一分钟的在线ip
        '''
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
            cursor.execute(
                'TRUNCATE TABLE {}'.format(cls._meta.db_table))

    @property
    def node_name(self):
        return Node.get_by_node_id(self.node_id).name

    node_id = models.IntegerField(verbose_name='节点id', blank=False, null=False)
    ip = models.CharField(verbose_name='设备ip', max_length=128)
    user = models.CharField(verbose_name='用户名', max_length=128)
    log_time = models.DateTimeField('日志时间', auto_now=True)

    class Meta:
        verbose_name_plural = '节点在线IP'
        ordering = ['-log_time']
