from PIL import Image
from django.db import models


# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=300, null=True, blank=True)
    industry = models.CharField(max_length=300, null=True, blank=True)
    about_us = models.TextField(null=True, blank=True)
    company_size = models.CharField(max_length=300, null=True, blank=True)
    headquarters = models.CharField(max_length=300, null=True, blank=True)
    specialities = models.TextField(max_length=300, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_image/', default='profile_image'
                                                                          '/default_company_profile_photo.jpeg', null=True, blank=True)
    cover_image = models.ImageField(upload_to='cover_photo/', default='cover_photo/default_company_cover_photo.jpeg', null=True, blank=True)

    # not in form
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super(Company, self).save()
        if self.cover_image:
            img = Image.open(self.cover_image.path)
            new_img = img.resize((1366, 400))
            new_img = new_img.convert('RGB')
            new_img.save(self.cover_image.path)
        if self.profile_image:
            img = Image.open(self.profile_image.path)
            new_img = img.resize((186, 182))
            new_img = new_img.convert('RGB')
            new_img.save(self.profile_image.path)
        super().save(*args, **kwargs)

    def get_profile_img(self):
        if self.profile_image:
            return self.profile_image.url
        else:
            return '/static/images/icon/user.png'

    def get_cover_img(self):
        if self.cover_image:
            return self.cover_image.url
        else:
            return '/static/images/icon/user.png'