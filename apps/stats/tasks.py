from apps import celery_app, utils
from apps.stats import models


@celery_app.task
def gen_daily_stats_task():
    """生成昨天的记录，和更新今天的记录"""
    today = utils.get_current_datetime()
    models.DailyStats.create_or_update_stats(today)
    models.DailyStats.create_or_update_stats(today.add(days=-1))
