from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from academy.permissions import ensure_role_groups


class Command(BaseCommand):
    help = 'Create a coach account. Coach accounts can only access attendance.'

    def add_arguments(self, parser):
        parser.add_argument('--username', help='Coach username')
        parser.add_argument('--email', default='', help='Coach email')
        parser.add_argument('--password', help='Coach password')

    def handle(self, *args, **options):
        User = get_user_model()
        _, coach_group = ensure_role_groups()

        username = options.get('username') or input('Coach username: ').strip()
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
        user.groups.add(coach_group)

        self.stdout.write(self.style.SUCCESS(f'Coach account "{username}" created successfully.'))
