from django.db import models


# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=300)
    industry = models.CharField(max_length=300)
    about_us = models.TextField()
    company_size = models.CharField(max_length=300)
    headquarters = models.CharField(max_length=300)
    specialities = models.TextField(max_length=300)
    profile_image = models.ImageField(upload_to='profile_image/', default='profile_image'
                                                                          '/default_company_profile_photo.jpeg')
    cover_image = models.ImageField(upload_to='cover_photo/', default='cover_photo/default_company_cover_photo.jpeg')

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
