from .common import BASE_DIR

# 定时任务相关
CRONJOBS = [
    (
        "*/1 * * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "check_user_state"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "0 0 1 * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "auto_reset_traffic"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "0 2 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_traffic_log"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "30 2 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_node_online_log"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "0 4 1 * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "reset_node_traffic"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "30 1 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_online_ip_log"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
    (
        "*/5 * * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "make_up_lost_order"},
        ">>" + BASE_DIR + "/logs/cron.log",
    ),
]
