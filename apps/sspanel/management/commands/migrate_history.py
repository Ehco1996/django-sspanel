from django.core.management.base import BaseCommand

from apps.sspanel.models import Goods, PurchaseHistory, User


class Command(BaseCommand):
    def handle(self, *args, **options):

        for h in PurchaseHistory.objects.all():
            good = Goods.objects.filter(name=h.good_name).first()
            user = User.objects.filter(username=h.user).first()
            if good:
                h.good_id = good.id
            if user:
                h.user_id = user.id
            h.save()
            print(f"updated: {h}")
