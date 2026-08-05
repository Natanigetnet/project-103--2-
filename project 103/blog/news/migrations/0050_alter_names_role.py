from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0049_sync_registrar_member_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='names',
            name='role',
            field=models.CharField(
                choices=[
                    ('trainer', 'Trainer'),
                    ('trainee', 'Trainee'),
                    ('registrar', 'Registrar'),
                ],
                default='trainee',
                max_length=10,
            ),
        ),
    ]
