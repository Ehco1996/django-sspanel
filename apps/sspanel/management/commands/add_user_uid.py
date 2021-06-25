import uuid

from django.core.management.base import BaseCommand

from apps.sspanel.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):

        for user in User.objects.all():
            user.uid = uuid.uuid4()
            user.save()
            print(f"save user={user}")
