from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0051_sync_all_registrar_member_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='names',
            name='category_changed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
