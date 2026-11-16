"""
Custom user model.

Roles:
  CUSTOMER          — public registration, can book non-VIP courts (or VIP if is_vip=True)
  COACH             — added by manager; can book courts like a customer in v0.1
  OPERATIONS_MANAGER — full manager dashboard access

The username field is replaced with email as the unique identifier.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra):
        extra.setdefault("role", User.OPERATIONS_MANAGER)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, full_name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    CUSTOMER = "CUSTOMER"
    COACH = "COACH"
    OPERATIONS_MANAGER = "OPERATIONS_MANAGER"
    ROLE_CHOICES = [
        (CUSTOMER, "Customer"),
        (COACH, "Coach"),
        (OPERATIONS_MANAGER, "Operations Manager"),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=CUSTOMER)
    is_vip = models.BooleanField(default=False)         # only meaningful for CUSTOMER
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)       # required by Django admin
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
