
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or reset the deployment admin account."

    def handle(self, *args, **options):
        username = os.environ.get("RESET_ADMIN_USERNAME")
        password = os.environ.get("RESET_ADMIN_PASSWORD")

        if not username or not password:
            raise CommandError(
                "Missing RESET_ADMIN_USERNAME or RESET_ADMIN_PASSWORD."
            )

        if len(password) < 12:
            raise CommandError("Password must be at least 12 characters.")

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user is None:
            user = User(username=username)

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS("Admin account created or reset.")
        )
