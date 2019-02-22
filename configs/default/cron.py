from .common import BASE_DIR

# 定时任务相关
CRONJOBS = [
    (
        "* 1 * * *",
        "commands.croncmds.check_user_state",
        ">>" + BASE_DIR + "/logs/userstate.log",
    ),
    (
        "0 0 1 * *",
        "commands.croncmds.auto_reset_traffic",
        ">>" + BASE_DIR + "/logs/trafficrest.log",
    ),  # 每月月初重置免费用户流量，日志写入logs
    (
        "0 2 * * *",
        "commands.croncmds.clean_traffic_log",
        ">>" + BASE_DIR + "/logs/trafficrest.log",
    ),  # 每天清空流量记录，日志写入logs
    (
        "30 2 * * *",
        "commands.croncmds.clean_online_log",
        ">>" + BASE_DIR + "/logs/node_online.log",
    ),  # 每天凌晨2:30删除节点在线记录，日志写入logs
    (
        "0 4 1 * *",
        "commands.croncmds.reset_node_traffic",
        ">>" + BASE_DIR + "/logs/node_reset.log",
    ),  # 每月第一天凌晨4点重置节点流量，日志写入logs
    (
        "30 1 * * *",
        "commands.croncmds.clean_online_ip_log",
        ">>" + BASE_DIR + "/logs/onlineip_reset.log",
    ),  # 每天凌晨1点半清空ip记录
    (
        "*/5 * * * *",
        "commands.croncmds.make_up_lost_order",  # 每隔五分钟检查一下有没有漏单
        ">>" + BASE_DIR + "/logs/check_orders.log",
    ),
]
