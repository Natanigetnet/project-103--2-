from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0020_alter_names_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='medical_info',
            field=models.TextField(blank=True, help_text='Medical notes, conditions, allergies, or emergency info'),
        ),
    ]
