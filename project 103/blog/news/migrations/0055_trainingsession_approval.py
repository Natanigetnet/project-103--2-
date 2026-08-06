from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0054_feedreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsession',
            name='approval_status',
            field=models.CharField(choices=[('pending', 'Pending approval'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10),
        ),
        migrations.AddField(
            model_name='trainingsession',
            name='rejection_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='trainingsession',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trainingsession',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_training_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunSQL(
            "UPDATE news_trainingsession SET approval_status = 'approved'",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
