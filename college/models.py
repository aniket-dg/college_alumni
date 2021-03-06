from django.db import models


# Create your models here.
class College(models.Model):
    code = models.CharField(max_length=300)
    name = models.CharField(max_length=300)
    domain = models.CharField(max_length=300, null=True, blank=True)
    def __str__(self):
        return f"college_{self.code}"
