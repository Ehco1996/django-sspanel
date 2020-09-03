from apps import celery_app
from apps.sspanel.models import User


@celery_app.task
def debug_task():
    u = User.objects.first()
    print("i am in debug", u)
