import decimal
from typing import List

import pendulum
from django.db import models

from apps import utils
from apps.proxy import models as pm
from apps.sspanel import models as sm


class DailyStats(models.Model):
    date = models.DateField(verbose_name="创建日期", unique=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    new_user_count = models.BigIntegerField(verbose_name="新用户数量", default=0)
    active_user_count = models.BigIntegerField(verbose_name="活跃户数量", default=0)
    checkin_user_count = models.BigIntegerField(verbose_name="签到用户数量", default=0)

    order_count = models.BigIntegerField(verbose_name="用户订单数量", default=0)
    order_amount = models.DecimalField(
        verbose_name="订单总金额",
        decimal_places=2,
        max_digits=10,
        default=decimal.Decimal(0),
    )
    cost_amount = models.DecimalField(
        verbose_name="订单总成本",
        decimal_places=2,
        max_digits=10,
        default=decimal.Decimal(0),
    )

    total_used_traffic = models.BigIntegerField(verbose_name="总流量GB", default=0)

    class Meta:
        verbose_name = "每日记录"
        verbose_name_plural = "每日记录"
        ordering = ["-date"]

    def __str__(self) -> str:
        return str(self.date)

    @classmethod
    def create_or_update_stats(cls, dt: pendulum.DateTime):
        date = dt.date()
        today = utils.get_current_datetime().date()
        log, _ = cls.objects.get_or_create(date=date)
        # 如果是今天之前的记录就不在更新了
        if date < today:
            return log

        log.new_user_count = sm.User.get_new_user_count_by_datetime(dt)
        log.active_user_count = pm.UserTrafficLog.get_active_user_count_by_datetime(dt)
        log.checkin_user_count = sm.UserCheckInLog.get_checkin_user_count(dt.date())

        log.order_count = sm.UserOrder.get_success_order_count(dt)
        log.order_amount = decimal.Decimal(sm.UserOrder.get_success_order_amount(dt))

        log.total_used_traffic = pm.UserTrafficLog.calc_traffic_by_datetime(dt)
        log.cost_amount = (
            pm.ProxyNode.calc_all_cost_price() + pm.RelayNode.calc_all_cost_price()
        ) / 30
        log.save()
        return log

    @classmethod
    def get_date_str_dict(cls, dt_list: List[pendulum.DateTime]):
        """NOTE key: date_str  value: log"""
        log_dict = {
            str(log.date): log
            for log in cls.objects.filter(date__in=[dt.date() for dt in dt_list])
        }

        for dt in dt_list:
            if not log_dict.get(str(dt.date())):
                log_dict[str(dt.date())] = cls.create_or_update_stats(dt)
        return log_dict
