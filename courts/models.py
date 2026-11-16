from django.db import models


class Court(models.Model):
    """
    The club has 3 courts, pre-seeded via a data migration.
    Court 1 is the VIP court — only VIP customers and managers can book it.
    """
    id = models.PositiveSmallIntegerField(primary_key=True)  # 1, 2, 3
    name = models.CharField(max_length=50)
    is_vip = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
