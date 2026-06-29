# Generated manually for QAURA Academy MVP weekly session plans.

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0002_player_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='plan_start_date',
            field=models.DateField(blank=True, null=True, verbose_name='Current Plan Start Date'),
        ),
        migrations.AddField(
            model_name='player',
            name='plan_sessions_count',
            field=models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Current Plan Sessions'),
        ),
    ]
