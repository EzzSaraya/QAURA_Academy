from datetime import time

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from academy.constants import ADMIN_GROUP_NAME, COACH_GROUP_NAME, DEFAULT_TRAINING_GROUPS
from academy.models import TrainingGroup


class Command(BaseCommand):
    help = 'Seed default training groups and staff role groups.'

    def handle(self, *args, **options):
        for group_data in DEFAULT_TRAINING_GROUPS:
            hours, minutes = [int(part) for part in group_data['time'].split(':')]
            group_time = time(hours, minutes)
            obj, created = TrainingGroup.objects.get_or_create(
                name=group_data['name'],
                defaults={'day': group_data['day'], 'time': group_time},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {obj}'))
            else:
                self.stdout.write(f'{obj} already exists')

        for group_name in [ADMIN_GROUP_NAME, COACH_GROUP_NAME]:
            Group.objects.get_or_create(name=group_name)
            self.stdout.write(self.style.SUCCESS(f'Role group ready: {group_name}'))
