from celery.schedules import crontab
from pendulum import Duration

# 定时任务相关
task_schedule = {
    "apps.sspanel.tasks.auto_reset_free_user_traffic_task": crontab(
        day_of_month=1, hour=0, minute=0
    ),
    "apps.sspanel.tasks.reset_node_traffic_task": crontab(
        day_of_month=1, hour=0, minute=0
    ),
    "apps.sspanel.tasks.check_user_state_task": Duration(minutes=1),
    "apps.sspanel.tasks.make_up_lost_order_task": Duration(seconds=15),
    "apps.sspanel.tasks.clean_traffic_log_task": Duration(minutes=1),
    "apps.sspanel.tasks.clean_online_ip_log_task": Duration(minutes=1),
    "apps.sspanel.tasks.clean_node_online_log_task": Duration(minutes=1),
    "apps.sspanel.tasks.clean_user_sub_log_task": Duration(minutes=1),
    # stats
    "apps.stats.tasks.gen_daily_stats_task": Duration(minutes=10),
}
