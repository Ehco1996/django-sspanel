from django.core.management.base import BaseCommand
from apps.sspanel.models import PurchaseHistory


class Command(BaseCommand):
    def handle(self, *args, **options):

        for log in PurchaseHistory.objects.all():
            log.good_name = log.good.name
            log.save()
            print(f"migrate log user:{log.user} good:{log.good}")
