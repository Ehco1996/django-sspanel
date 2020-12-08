"""
tianyi: 天一是三渣的早期作品:<贩罪>的主角，是像猫一样生活的男人，并且善于计算人心/性，做出各种冷静的数据分析
这里存一些数据分析相关的东西
"""
import decimal

from django.conf import settings
from django.db import models

from apps import utils
from apps.proxy import models as pm
from apps.sspanel import models as sm


class DashBoardManger:
    """
    无情的dashboard生成器

    TODO 每日/每小时使用流量统计
    """

    @classmethod
    def _gen_userorder_bar_chart_configs(cls, date_list):
        """获取指定日期的的订单统计"""
        bar_config = {
            "labels": [f"{date.month}-{date.day}" for date in date_list],
            "data": [
                sm.UserOrder.objects.filter(
                    created_at__range=[
                        t.start_of("day"),
                        t.end_of("day"),
                    ]
                ).count()
                for t in date_list
            ],
            "data_title": "每日订单数量",
        }
        return bar_config

    @classmethod
    def _gen_user_line_chart_configs(cls, date_list):
        active_user_count = [
            pm.UserTrafficLog.get_user_count_by_date(date) for date in date_list
        ]
        active_user_line_config = {
            "title": f"最近{len(date_list)}天 总活跃人数为{sum(active_user_count)}人",
            "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
            "data": active_user_count,
            "data_title": "活跃用户",
            "x_label": f"日期 最近{len(date_list)}天",
            "y_label": "人",
        }
        new_user_count = [
            sm.User.get_new_user_count_by_date(date) for date in date_list
        ]
        new_user_line_config = {
            "title": f"最近{len(date_list)}天 新增人数为{sum(new_user_count)}人",
            "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
            "data": new_user_count,
            "data_title": "新增用户",
            "x_label": f"日期 最近{len(date_list)}天",
            "y_label": "人",
        }
        return {
            "active_user_line_config": active_user_line_config,
            "new_user_line_config": new_user_line_config,
        }

    @classmethod
    def get_user_last_week_status_data(cls):
        """统计用户信息"""
        user_status = [
            pm.NodeOnlineLog.get_all_node_online_user_count(),
            sm.User.get_today_register_user().count(),
            sm.UserCheckInLog.get_today_checkin_user_count(),
        ]
        data = {"user_status": user_status}
        now = utils.get_current_datetime()
        last_week = [now.subtract(days=i) for i in range(6, -1, -1)]
        data.update(cls._gen_user_line_chart_configs(last_week))
        return data

    @classmethod
    def get_userorder_last_week_status_data(cls):
        """获取最近一周的订单统计数据
        1. 一周的订单趋势
        2. 一周的收入统计
        3. 今日的收入统计
        """
        now = utils.get_current_datetime()
        last_week = [now.subtract(days=i) for i in range(6, -1, -1)]
        today_amount = (
            sm.UserOrder.objects.filter(
                status=sm.UserOrder.STATUS_FINISHED,
                created_at__range=[
                    now.start_of("day"),
                    now.end_of("day"),
                ],
            ).aggregate(amount=models.Sum("amount"))["amount"]
            or "0"
        )
        week_amount = (
            sm.UserOrder.objects.filter(
                status=sm.UserOrder.STATUS_FINISHED,
                created_at__range=[
                    last_week[0].start_of("day"),
                    last_week[-1].end_of("day"),
                ],
            ).aggregate(amount=models.Sum("amount"))["amount"]
            or "0"
        )
        return {
            "bar_chart_configs": cls._gen_userorder_bar_chart_configs(last_week),
            "amount_status": [
                int(decimal.Decimal(week_amount)),
                int(decimal.Decimal(today_amount)),
            ],
        }

    @classmethod
    def get_node_status(cls):
        active_nodes = pm.ProxyNode.get_active_nodes()
        return {
            "names": [node.name for node in active_nodes],
            "traffics": [
                round(node.used_traffic / settings.GB, 2) for node in active_nodes
            ],
        }
