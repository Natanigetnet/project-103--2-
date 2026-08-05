from django.db import migrations


def sync_all_registrar_member_roles(apps, schema_editor):
    Names = apps.get_model('news', 'names')
    UserProfile = apps.get_model('news', 'UserProfile')

    registrar_emails = {
        email.lower()
        for email in UserProfile.objects.filter(role='registrar')
        .values_list('user__email', flat=True)
        if email
    }

    for member in Names.objects.exclude(role='registrar'):
        if member.email and member.email.lower() in registrar_emails:
            member.role = 'registrar'
            member.save(update_fields=['role'])


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0050_alter_names_role'),
    ]

    operations = [
        migrations.RunPython(sync_all_registrar_member_roles, migrations.RunPython.noop),
    ]
