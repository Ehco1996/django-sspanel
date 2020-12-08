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
    """

    @classmethod
    def get_user_last_week_status_data(cls):
        """统计用户信息"""

        def gen_line_configs(date_list):
            active_user_count = [
                pm.UserTrafficLog.get_active_user_count_by_date(date)
                for date in date_list
            ]
            active_user_line_config = {
                "title": f"最近{len(date_list)}天 总活跃人数为{sum(active_user_count)}人",
                "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
                "data": active_user_count,
                "data_title": "活跃用户",
                "x_label": f"最近{len(date_list)}天",
                "y_label": "活跃用户数",
            }
            new_user_count = [
                sm.User.get_new_user_count_by_date(date) for date in date_list
            ]
            new_user_line_config = {
                "title": f"最近{len(date_list)}天 新增人数为{sum(new_user_count)}人",
                "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
                "data": new_user_count,
                "data_title": "新增用户",
                "x_label": f"最近{len(date_list)}天",
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
                sm.UserCheckInLog.get_today_checkin_user_count(),
            ]
            return {
                "title": f"总用户数量{sm.User.objects.all().count()}人",
                "labels": ["在线人数", "今日注册", "今日签到"],
                "data": user_status,
                "data_title": "活跃用户",
            }

        data = {"doughnut_config": gen_doughnut_config()}
        last_week = utils.gen_date_list(utils.get_current_datetime())
        data.update(gen_line_configs(last_week))
        return data

    @classmethod
    def get_userorder_last_week_status_data(cls):
        """获取最近一周的订单统计数据
        1. 一周的订单趋势
        2. 一周的收入统计
        3. 今日的收入统计
        """

        def gen_bar_config(date_list):
            success_order_count = [
                sm.UserOrder.get_success_order_count(t) for t in date_list
            ]
            bar_config = {
                "title": f"一周总订单数量:{sum(success_order_count)}",
                "labels": [f"{date.month}-{date.day}" for date in date_list],
                "data": success_order_count,
                "data_title": "每日订单数量",
                "x_label": f"最近{len(date_list)}天",
                "y_label": "订单数量",
            }
            return bar_config

        def gen_doughnut_config():
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
                "title": "收入分析 单位:元",
                "labels": ["一周收入", "今日收入"],
                "data": [
                    int(decimal.Decimal(week_amount)),
                    int(decimal.Decimal(today_amount)),
                ],
                "data_title": "收入分析",
            }

        now = utils.get_current_datetime()
        last_week = utils.gen_date_list(now)

        return {
            "bar_config": gen_bar_config(last_week),
            "doughnut_config": gen_doughnut_config(),
        }

    @classmethod
    def get_node_status(cls):
        def gen_line_config(date_list):
            node_total_traffic = pm.ProxyNode.calc_total_traffic()
            line_config = {
                "title": f"所有节点当月共消耗:{node_total_traffic}",
                "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
                "data": [
                    pm.UserTrafficLog._calc_traffic_by_date(date) for date in date_list
                ],
                "data_title": "每日流量(GB)",
                "x_label": f"最近{len(date_list)}天",
                "y_label": "单位:GB",
            }
            return line_config

        def gen_doughnut_config():
            active_nodes = pm.ProxyNode.get_active_nodes()
            return {
                "title": "节点流量 单位:GB",
                "labels": [node.name for node in active_nodes],
                "data": [
                    round(node.used_traffic / settings.GB, 2) for node in active_nodes
                ],
                "data_title": "节点流量",
            }

        date_list = utils.gen_date_list(utils.get_current_datetime())
        return {
            "doughnut_config": gen_doughnut_config(),
            "line_config": gen_line_config(date_list),
        }

    @classmethod
    def gen_traffic_line_chart_configs(cls, user_id, node_id, date_list):
        proxy_node = pm.ProxyNode.get_or_none(node_id)  # node must exists
        user_total_traffic = pm.UserTrafficLog.calc_user_total_traffic(
            proxy_node, user_id
        )
        date_list = sorted(date_list)
        line_config = {
            "title": "节点 {} 当月共消耗：{}".format(proxy_node.name, user_total_traffic),
            "labels": ["{}-{}".format(t.month, t.day) for t in date_list],
            "data": [
                pm.UserTrafficLog.calc_traffic_by_date(user_id, proxy_node, date)
                for date in date_list
            ],
            "data_title": proxy_node.name,
            "x_label": f"最近{len(date_list)}天",
            "y_label": "单位:GB",
        }
        return line_config

    @classmethod
    def gen_ref_log_bar_chart_configs(cls, user_id, date_list):
        """set register_count to 0 if the query date log not exists"""
        date_list = sorted(date_list)
        logs = {
            log.date: log.register_count
            for log in sm.UserRefLog.list_by_user_id_and_date_list(user_id, date_list)
        }
        bar_config = {
            "title": f"总共邀请用户:{sm.UserRefLog.calc_user_total_ref_count(user_id)}人",
            "labels": [f"{date.month}-{date.day}" for date in date_list],
            "data": [logs.get(date, 0) for date in date_list],
            "data_title": "每日邀请注册人数",
            "x_label": f"最近{len(date_list)}天",
            "y_label": "人",
        }
        return bar_config
