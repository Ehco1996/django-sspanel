# 定时任务相关
CRONJOBS = [
    (
        "0 0 1 * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "auto_reset_traffic"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "1 0 1 * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "reset_node_traffic"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "0 2 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_traffic_log"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "30 2 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_node_online_log"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "30 1 * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "clean_online_ip_log"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "*/5 * * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "make_up_lost_order"},
        ">>" + "/var/log/django-cron.log",
    ),
    (
        "*/1 * * * *",
        "django.core.management.call_command",
        ["run_cron_job"],
        {"jobname": "check_user_state"},
        ">>" + "/var/log/django-cron.log",
    ),
]
