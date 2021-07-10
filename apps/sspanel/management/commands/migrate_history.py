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


def create_random_order(n=100):

    from apps.sspanel.models import User, UserOrder
    from apps.utils import get_current_datetime

    user = User.objects.first()
    for i in range(n):
        order = UserOrder.objects.create(
            user=user,
            status=UserOrder.STATUS_CREATED,
            out_trade_no=UserOrder.gen_out_trade_no(),
            amount="100",
            qrcode_url="qrcode_url",
            expired_at=get_current_datetime().add(minutes=10),
        )
        print(order)
