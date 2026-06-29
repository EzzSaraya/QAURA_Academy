# Generated manually for QAURA Academy player phone and editable end date.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0003_player_plan_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='phone_number',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='Phone Number'),
        ),
        migrations.AddField(
            model_name='player',
            name='plan_end_date_manual',
            field=models.DateField(blank=True, null=True, verbose_name='Current Plan End Date'),
        ),
    ]
