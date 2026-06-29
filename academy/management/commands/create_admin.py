from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from academy.permissions import ensure_role_groups


class Command(BaseCommand):
    help = 'Create an admin account. Owner/superuser can also do this from the website.'

    def add_arguments(self, parser):
        parser.add_argument('--username', help='Admin username')
        parser.add_argument('--email', default='', help='Admin email')
        parser.add_argument('--password', help='Admin password')

    def handle(self, *args, **options):
        User = get_user_model()
        admin_group, _ = ensure_role_groups()

        username = options.get('username') or input('Admin username: ').strip()
        if not username:
            raise CommandError('Username is required.')

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists.')

        email = options.get('email', '')
        password = options.get('password')
        if not password:
            password = getpass('Password: ')
            password2 = getpass('Password again: ')
            if password != password2:
                raise CommandError('Passwords do not match.')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = True
        user.is_superuser = False
        user.save(update_fields=['is_staff', 'is_superuser'])
        user.groups.add(admin_group)

        self.stdout.write(self.style.SUCCESS(f'Admin account "{username}" created successfully.'))
