from uuid import uuid4

from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from django.db import transaction
from apps.sspanel.models import User


class Command(createsuperuser.Command):
    help = """
            创建管理员账户 EXAMPLE
            python manage.py  create_admin --email "admin@ss.com" --username "admin" --password "adminadmin"
           """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help="Specifies the password for the superuser.",
        )

    def handle(self, *args, **options):
        options.setdefault("interactive", False)
        database = options.get("database")
        password = options.get("password")
        username = options.get("username")
        email = options.get("email")

        if not password or not username or not email:
            raise CommandError("--email --username and --password are required options")

        error_msg = self._validate_username(username, "username", database)
        if error_msg:
            raise CommandError(error_msg)

        user_data = {
            "username": username,
            "password": password,
            "email": email,
            "vmess_uuid": str(uuid4()),
            "ss_password": User.get_not_used_port(),
        }

        with transaction.atomic():
            user = self.UserModel._default_manager.db_manager(
                database
            ).create_superuser(**user_data)
        if options.get("verbosity", 0) >= 1:
            self.stdout.write(f"Admin: {user} created successfully.")
