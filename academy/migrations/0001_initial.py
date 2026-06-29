# Generated for QAURA Academy MVP

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('day', models.CharField(max_length=20)),
                ('time', models.TimeField()),
            ],
            options={
                'ordering': ['day', 'time'],
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('total_sessions', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('remaining_sessions', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='players', to='academy.traininggroup')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('status', models.CharField(choices=[('attend', 'Attend'), ('absent', 'Absent')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attendance_records', to='academy.traininggroup')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='academy.player')),
            ],
            options={
                'ordering': ['-date', 'player__name'],
            },
        ),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=('player', 'date'), name='one_attendance_per_player_per_day'),
        ),
    ]
