"""
tianyi: 天一是三渣的早期作品:<贩罪>的主角，是像猫一样生活的男人，并且善于计算人心/性，做出各种冷静的数据分析
这里存一些数据分析相关的东西
"""
import decimal
from typing import List

import pendulum
from django.conf import settings
from django.db import models

from apps import utils
from apps.proxy import models as pm
from apps.sspanel import models as sm
from apps.stats.models import DailyStats


class DashBoardManger:
    """
    无情的dashboard生成器
    """

    def __init__(self, dt_list: List[pendulum.DateTime]):
        self.dt_list = dt_list
        self.log_dict = DailyStats.get_date_str_dict(dt_list)

    def _get_by_dt(self, dt: pendulum.DateTime):
        return self.log_dict[str(dt.date())]

    def get_node_status(self):
        def gen_bar_config(dt_list):
            node_total_traffic = pm.ProxyNode.calc_total_traffic()
            bar_config = {
                "title": f"所有节点当月共消耗:{node_total_traffic}",
                "labels": ["{}-{}".format(t.month, t.day) for t in dt_list],
                "data": [self._get_by_dt(dt).total_used_traffic for dt in dt_list],
                "data_title": "每日流量(GB)",
                "x_label": f"最近{len(dt_list)}天",
                "y_label": "单位:GB",
            }
            return bar_config

        def gen_doughnut_config():
            active_nodes = pm.ProxyNode.get_active_nodes()
            labels = [node.name for node in active_nodes]
            return {
                "title": f"总共{len(labels)}条节点",
                "labels": labels,
                "data": [
                    round(node.used_traffic / settings.GB, 2) for node in active_nodes
                ],
                "data_title": "节点流量",
            }

        return {
            "doughnut_config": gen_doughnut_config(),
            "bar_config": gen_bar_config(self.dt_list),
        }

    def get_user_status_data(self):
        """统计用户信息"""

        def gen_line_configs(dt_list):
            active_user_count = [
                self._get_by_dt(dt).active_user_count for dt in dt_list
            ]
            active_user_line_config = {
                "title": f"最近{len(dt_list)}天 总活跃人数为{sum(active_user_count)}人",
                "labels": ["{}-{}".format(t.month, t.day) for t in dt_list],
                "data": active_user_count,
                "data_title": "活跃用户",
                "x_label": f"最近{len(dt_list)}天",
                "y_label": "活跃用户数",
            }
            new_user_count = [self._get_by_dt(dt).new_user_count for dt in dt_list]
            new_user_line_config = {
                "title": f"最近{len(dt_list)}天 新增人数为{sum(new_user_count)}人",
                "labels": ["{}-{}".format(t.month, t.day) for t in dt_list],
                "data": new_user_count,
                "data_title": "新增用户",
                "x_label": f"最近{len(dt_list)}天",
                "y_label": "新用户数",
            }
            return {
                "active_user_line_config": active_user_line_config,
                "new_user_line_config": new_user_line_config,
            }

        def gen_doughnut_config():
            user_status = [
                pm.NodeOnlineLog.get_all_node_online_user_count(),
                sm.User.get_today_register_user().count(),
                sm.UserCheckInLog.get_checkin_user_count(
                    utils.get_current_datetime().date()
                ),
            ]
            return {
                "title": f"总用户数量{sm.User.objects.all().count()}人",
                "labels": ["在线人数", "今日注册", "今日签到"],
                "data": user_status,
                "data_title": "活跃用户",
            }

        data = {"doughnut_config": gen_doughnut_config()}
        data.update(gen_line_configs(self.dt_list))
        return data

    def get_userorder_status_data(self):
        """获取的订单统计数据"""

        def gen_bar_config(dt_list):
            success_order_count = [self._get_by_dt(dt).order_count for dt in dt_list]
            bar_config = {
                "title": f"总订单数量:{sum(success_order_count)}",
                "labels": [f"{date.month}-{date.day}" for date in dt_list],
                "data": success_order_count,
                "data_title": "每日订单数量",
                "x_label": f"最近{len(dt_list)}天",
                "y_label": "订单数量",
            }
            return bar_config

        def gen_doughnut_config(dt_list):
            now = utils.get_current_datetime()
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
            total_amount = (
                sm.UserOrder.objects.filter(
                    status=sm.UserOrder.STATUS_FINISHED,
                    created_at__range=[
                        dt_list[0].start_of("day"),
                        dt_list[-1].end_of("day"),
                    ],
                ).aggregate(amount=models.Sum("amount"))["amount"]
                or "0"
            )
            return {
                "title": f"总收入{total_amount}元",
                "labels": ["总收入", "今日收入"],
                "data": [
                    int(decimal.Decimal(total_amount)),
                    int(decimal.Decimal(today_amount)),
                ],
                "data_title": "收入分析",
            }

        def gen_line_config(dt_list):
            amount_data = [self._get_by_dt(dt).order_amount for dt in dt_list]
            order_amount_line_config = {
                "title": f"最近{len(dt_list)}天 总收益为{sum(amount_data)}元",
                "labels": ["{}-{}".format(t.month, t.day) for t in dt_list],
                "data": amount_data,
                "data_title": "收益",
                "x_label": f"最近{len(dt_list)}天",
                "y_label": "金额/元",
            }
            return order_amount_line_config

        return {
            "bar_config": gen_bar_config(self.dt_list),
            "doughnut_config": gen_doughnut_config(self.dt_list),
            "line_config": gen_line_config(self.dt_list),
        }

    @classmethod
    def gen_traffic_line_chart_configs(cls, user_id, node_id, dt_list):
        proxy_node = pm.ProxyNode.get_or_none(node_id)  # node must exists
        user_total_traffic = pm.UserTrafficLog.calc_user_total_traffic(
            proxy_node, user_id
        )
        dt_list = sorted(dt_list)
        line_config = {
            "title": "节点 {} 当月共消耗：{}".format(proxy_node.name, user_total_traffic),
            "labels": ["{}-{}".format(t.month, t.day) for t in dt_list],
            "data": [
                pm.UserTrafficLog.calc_traffic_by_datetime(dt, user_id, proxy_node)
                for dt in dt_list
            ],
            "data_title": proxy_node.name,
            "x_label": f"最近{len(dt_list)}天",
            "y_label": "单位:GB",
        }
        return line_config

    @classmethod
    def gen_ref_log_bar_chart_configs(cls, user_id, dt_list):
        """set register_count to 0 if the query date log not exists"""
        dt_list = sorted(dt_list)
        logs = {
            log.date: log.register_count
            for log in sm.UserRefLog.list_by_user_id_and_date_list(user_id, dt_list)
        }
        bar_config = {
            "title": f"总共邀请用户:{sm.UserRefLog.calc_user_total_ref_count(user_id)}人",
            "labels": [f"{date.month}-{date.day}" for date in dt_list],
            "data": [logs.get(date, 0) for date in dt_list],
            "data_title": "每日邀请注册人数",
            "x_label": f"最近{len(dt_list)}天",
            "y_label": "人",
        }
        return bar_config
