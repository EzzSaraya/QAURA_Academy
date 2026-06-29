# Generated manually for QAURA Academy MVP update.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='The login account used by the player.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='player_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='player',
            name='player_id',
            field=models.CharField(max_length=50, unique=True, verbose_name='Player Code'),
        ),
    ]
