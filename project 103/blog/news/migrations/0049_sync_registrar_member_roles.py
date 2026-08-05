from django.db import migrations


def sync_registrar_member_roles(apps, schema_editor):
    Names = apps.get_model('news', 'names')
    UserProfile = apps.get_model('news', 'UserProfile')

    registrar_emails = {
        email.lower()
        for email in UserProfile.objects.filter(role='registrar')
        .values_list('user__email', flat=True)
        if email
    }

    for member in Names.objects.filter(role='trainer'):
        if member.email and member.email.lower() in registrar_emails:
            member.role = 'registrar'
            member.save(update_fields=['role'])


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0048_feedpost'),
    ]

    operations = [
        migrations.RunPython(sync_registrar_member_roles, migrations.RunPython.noop),
    ]
