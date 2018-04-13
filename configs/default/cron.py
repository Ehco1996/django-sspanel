from .common import BASE_DIR

# 定时任务相关
CRONJOBS = [
    ('* * * * *', 'apps.ssserver.views.check_user_state',
     '>>' + BASE_DIR + '/logs/userstate.log'),  # 每天23.59分检测用户等级是否到期，日志写入logs
    ('0 0 1 * *', 'apps.ssserver.views.auto_reset_traffic',
     '>>' + BASE_DIR + '/logs/trafficrest.log'),  # 每月月初重置免费用户流量，日志写入logs
    ('15 12 * * 1', 'apps.ssserver.views.clean_traffic_log',
     '>>' + BASE_DIR + '/logs/trafficrest.log'),  # 每周一清空流量记录，日志写入logs
    ('30 2 * * *', 'apps.ssserver.views.clean_online_log',
     '>>' + BASE_DIR + '/logs/node_online.log'),  # 每天凌晨2:30删除节点在线记录，日志写入logs
    ('0 3 1 * *', 'apps.ssserver.views.clean_node_log',
     '>>' + BASE_DIR + '/logs/node_info.log'),  # 每月第一天凌晨3点删除所有节点负载，日志写入logs
    ('0 4 1 * *', 'apps.ssserver.views.reset_node_traffic',
     '>>' + BASE_DIR + '/logs/node_reset.log'),  # 每月第一天凌晨4点重置节点流量，日志写入logs
    ('30 1 * * *', 'apps.ssserver.views.clean_online_ip_log',
     '>>' + BASE_DIR + '/logs/onlineip_reset.log'),  # 每天凌晨1点半清空ip记录
]
