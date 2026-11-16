"""
Management command: seed_demo

Creates demo accounts so you can immediately test the full frontend without
signing up manually.

  python manage.py seed_demo

Accounts created (skipped if they already exist):
  manager@nyarutarama.rw / manager123    — OPERATIONS_MANAGER
  alice@example.com     / customer123   — CUSTOMER (non-VIP)
  vip@example.com       / customer123   — CUSTOMER (VIP)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

DEMO_USERS = [
    {
        "email": "manager@nyarutarama.rw",
        "full_name": "Club Manager",
        "phone": "+250788000001",
        "password": "manager123",
        "role": User.OPERATIONS_MANAGER,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "alice@example.com",
        "full_name": "Alice Uwase",
        "phone": "+250788000002",
        "password": "customer123",
        "role": User.CUSTOMER,
        "is_vip": False,
    },
    {
        "email": "vip@example.com",
        "full_name": "Bob Nkurunziza",
        "phone": "+250788000003",
        "password": "customer123",
        "role": User.CUSTOMER,
        "is_vip": True,
    },
]


class Command(BaseCommand):
    help = "Seed demo user accounts for local development"

    def handle(self, *args, **options):
        for data in DEMO_USERS:
            email = data["email"]
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  skip  {email} (already exists)")
                continue
            User.objects.create_user(
                email=email,
                full_name=data["full_name"],
                phone=data.get("phone", ""),
                password=data["password"],
                role=data.get("role", User.CUSTOMER),
                is_vip=data.get("is_vip", False),
                is_staff=data.get("is_staff", False),
                is_superuser=data.get("is_superuser", False),
            )
            self.stdout.write(self.style.SUCCESS(f"  created {email}"))
        self.stdout.write(self.style.SUCCESS("Done."))
