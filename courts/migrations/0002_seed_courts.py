"""Seed the three courts that match the frontend's clubData.js."""
from django.db import migrations


def seed_courts(apps, schema_editor):
    Court = apps.get_model("courts", "Court")
    courts = [
        {"id": 1, "name": "Court 1", "is_vip": True, "description": "VIP clay court with premium facilities."},
        {"id": 2, "name": "Court 2", "is_vip": False, "description": "Hard court, open to all members."},
        {"id": 3, "name": "Court 3", "is_vip": False, "description": "Hard court, open to all members."},
    ]
    for c in courts:
        Court.objects.update_or_create(id=c["id"], defaults=c)


def unseed_courts(apps, schema_editor):
    Court = apps.get_model("courts", "Court")
    Court.objects.filter(id__in=[1, 2, 3]).delete()


class Migration(migrations.Migration):
    dependencies = [("courts", "0001_initial")]
    operations = [migrations.RunPython(seed_courts, unseed_courts)]
