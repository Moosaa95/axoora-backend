import os
from typing import Any
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Creates a default superuser for Axoora Django admin if one does not exist.'

    def handle(self, *args, **options):
        User: Any = get_user_model()
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@axoora.ai')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123456')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"✓ Superuser '{username}' created successfully with password '{password}'."))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
