from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0052_names_category_changed_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='gymconfig',
            name='subscription_grace_days',
            field=models.PositiveIntegerField(default=0, help_text='Days after expiry before account deactivation'),
        ),
        migrations.AddField(
            model_name='gymconfig',
            name='subscription_months',
            field=models.PositiveIntegerField(default=3, help_text='Membership duration in months'),
        ),
    ]
