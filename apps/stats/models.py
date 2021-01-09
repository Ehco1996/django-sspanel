import pendulum
from django.db import models

from apps import utils
from apps.proxy import models as pm
from apps.sspanel import models as sm


class DailyStats(models.Model):

    date = models.DateField(auto_now_add=True, verbose_name="创建日期", unique=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    new_user_count = models.BigIntegerField(verbose_name="新用户数量", default=0)
    active_user_count = models.BigIntegerField(verbose_name="活跃户数量", default=0)
    checkin_user_count = models.BigIntegerField(verbose_name="签到用户数量", default=0)

    order_count = models.BigIntegerField(verbose_name="用户订单数量", default=0)
    order_amount = models.DecimalField(
        verbose_name="订单总金额", decimal_places=2, max_digits=2
    )

    total_used_traffic = models.BigIntegerField(verbose_name="总流量", default=0)

    class Meta:
        verbose_name = "每日记录"
        verbose_name_plural = "每日记录"
        ordering = ["-date"]

    @classmethod
    def create_or_update_stats(cls, date: pendulum.Date):
        today = utils.get_current_datetime().date()
        log, created = cls.objects.get_or_create(date=date)
        # 如果是今天之前的记录就不在更新了
        if not created and date < today:
            return log

        log.new_user_count = sm.User.get_new_user_count_by_date(date)
        log.active_user_count = pm.UserTrafficLog.get_active_user_count_by_date(date)
        log.checkin_user_count = sm.UserCheckInLog.get_checkin_user_count(date)

        log.order_count = sm.UserOrder.get_success_order_count(date)
        log.order_amount = sm.UserOrder.get_success_order_amount(date)

        log.total_used_traffic = pm.UserTrafficLog.calc_traffic_by_date(date)
        log.save()
