import os
import uuid
from io import BytesIO

import PIL
from PIL import Image
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

# Create your models here.
from chat.models import GroupChatModel
from college_alumni.settings import BASE_DIR
from industry.models import Company
from users.managers import UserManager
from django.core.files import File

REQUEST_CHOICES = (
    ('Process', 'Process'),
    ('Accepted', 'Accepted'),
    ('Declined', 'Declined'),
)


class UserBasic(models.Model):
    dob = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=300)
    country = models.CharField(max_length=300)
    about_me = models.TextField(null=True, blank=True)
    # user = models.ForeignKey('users.User', blank=True, null=True, on_delete=models.SET_NULL)


class BranchName(models.Model):
    name = models.CharField(max_length=300)


class CollegeName(models.Model):
    name = models.CharField(max_length=300)
    branches = models.ManyToManyField(BranchName, blank=True)
    about_us = models.TextField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='college_logo', default='profile_image/default_profile_image.png')
    website = models.URLField(null=True, blank=True)
    college_users = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    cover_image = models.ImageField(upload_to='cover_photo/', default='cover_photo/default_cover_photo.jpg')

    phone_number = models.BigIntegerField(help_text='Provide an mobile number with country code!', unique=True,
                                              null=True, blank=True)

    def save(self, *args, **kwargs):
        super(CollegeName, self).save()
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


class UserEducation(models.Model):
    college = models.ForeignKey(CollegeName, on_delete=models.CASCADE)
    admission_year = models.IntegerField()
    passout_year = models.IntegerField()
    current_city = models.CharField(max_length=300)
    branch = models.CharField(max_length=300)
    current_status = models.TextField(null=True, blank=True)
    current_company = models.ForeignKey('industry.Company', null=True, blank=True, on_delete=models.SET_NULL)
    # user = models.ForeignKey('users.User', blank=True, null=True, on_delete=models.SET_NULL)


class Interest(models.Model):
    name = models.CharField(max_length=300)


class UserInterest(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    interest = models.ManyToManyField(Interest, blank=True)
    # user = models.ForeignKey('users.User', blank=True, null=True, on_delete=models.SET_NULL)


class User(AbstractBaseUser, PermissionsMixin):
    # Required
    username = models.CharField(_('User Name'), unique=True, max_length=200)
    email = models.EmailField(_('Email'), unique=True, max_length=320, help_text='Provide an email for registration')
    college_code = models.CharField(max_length=300, null=True, blank=True)
    # Optional
    phone_number = models.BigIntegerField(help_text='Provide an mobile number with country code!', unique=True,
                                          null=True, blank=True)
    account_type = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(_('First Name'), max_length=200, null=True, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=300, null=True, blank=True)
    bio = models.TextField(max_length=300, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_image/', default='profile_image/default_profile_image.png')
    cover_image = models.ImageField(upload_to='cover_photo/', default='cover_photo/default_cover_photo.jpg')
    connections = models.ManyToManyField('users.Connection', blank=True)
    pending_connections = models.ManyToManyField('users.Connection', blank=True,
                                                 related_name='pending_user_connections')
    groups = models.ManyToManyField('chat.GroupChatModel', blank=True)
    uploaded_document = models.FileField(upload_to='documents', null=True, blank=True)
    # Django
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=False)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_staff = models.BooleanField(_('staff'), default=False)

    user_type = models.CharField(max_length=100, default='student')
    objects = UserManager()

    is_basic_info = models.BooleanField(default=False)
    user_basic = models.ForeignKey(UserBasic, null=True, blank=True, on_delete=models.SET_NULL)
    is_work_education = models.BooleanField(default=False)
    education = models.ForeignKey(UserEducation, null=True, blank=True, on_delete=models.SET_NULL)
    is_interest = models.BooleanField(default=False)
    user_interest = models.ForeignKey(UserInterest, null=True, blank=True, on_delete=models.SET_NULL)

    is_declined = models.BooleanField(default=False)
    reason_for_declined = models.TextField(null=True, blank=True)
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_website(self):
        if self.is_college_user_profile():
            if self.get_college_obj().website:
                return self.get_college_obj().website
            return 'N.A.'
        elif self.is_industry_user_profile():
            if self.get_industry_obj().website:
                return self.get_industry_obj().website
            return "N.A."
        return "N.A."


    def is_info_save(self):
        if self.is_basic_info and self.is_work_education and self.is_interest:
            return True
        return False

    def save(self, *args, **kwargs):
        super(User, self).save()
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

    def get_full_name(self):
        if self.is_industry_user_profile():
            if self.get_industry_obj().name:
                return self.get_industry_obj().name
        if self.is_college_user_profile():
            if self.get_college_obj().name:
                return self.get_college_obj().name

        return f"{self.first_name} {self.last_name}"

    def get_user_type(self):
        if self.is_college_user_profile():
            return "College Admin"
        elif self.is_industry_user_profile():
            return "Industry User"
        elif self.is_superuser:
            return "Super Admin"
        return "Student"

    def get_short_name(self):
        return self.first_name

    def get_user_connected_users(self):
        emails1 = []
        if self.is_superuser:
            emails1 = [user.email for user in User.objects.all().exclude(email=self.email)]
        if self.is_college_user() or self.is_industry_user():
            emails1 = [user.email for user in User.objects.filter(user_type='student').exclude(email=self.email)]


        emails = [user.connection_user.email for user in self.connections.filter(send_request="Accepted")]
        pending_emails = [user.connection_user.email for user in
                          self.pending_connections.filter(send_request="Accepted")]
        extra_email = [user.email for user in User.objects.filter(Q(user_type='college') |
                                                                  Q(user_type='industry') |
                                                                  Q(is_superuser=True), is_verified=True
                                                                  )]
        emails = emails1 + emails + pending_emails + extra_email
        emails = list(set(emails))
        users = User.objects.exclude(email=self.email).filter(email__in=emails)
        return users

    def get_user_connected_users_profile(self):
        # if self.is_superuser:
        #     return User.objects.all().exclude(email=self.email)
        # if self.is_college_user() or self.is_industry_user():
        #     return User.objects.filter(user_type='student').exclude(email=self.email)

        emails = [user.connection_user.email for user in self.connections.filter(send_request="Accepted")]
        pending_emails = [user.connection_user.email for user in
                          self.pending_connections.filter(send_request="Accepted")]
        # extra_email = [user.email for user in User.objects.filter(Q(user_type='college') |
        #                                                           Q(user_type='industry') |
        #                                                           Q(is_superuser=True), is_verified=True
        #                                                           )]
        emails = emails + pending_emails #+ extra_email
        emails = list(set(emails))
        users = User.objects.exclude(email=self.email).filter(email__in=emails)
        return users

    def get_user_groups_count(self):
        return self.groups.all().count()

    def get_user_connected_users_count(self):
        emails = [user.connection_user.email for user in self.connections.filter(send_request="Accepted")]
        pending_emails = [user.connection_user.email for user in
                          self.pending_connections.filter(send_request="Accepted")]
        emails = emails + pending_emails
        users = User.objects.exclude(email=self.email).filter(email__in=emails).count()
        return users

    def get_user_requested_users(self):
        users = self.connections.filter(request=True, send_request="Process")
        emails = [user.connection_user.email for user in users]
        users = User.objects.exclude(email=self.email).filter(email__in=emails)
        return users

    def get_user_requested_users_count(self):
        users = self.connections.filter(request=True, send_request="Process")
        emails = [user.connection_user.email for user in users]
        users = User.objects.exclude(email=self.email).filter(email__in=emails).count()
        return users

    def get_user_received_users(self):
        users = self.pending_connections.filter(request=True, send_request="Process")
        emails = [user.connection_user.email for user in users]
        users = User.objects.exclude(email=self.email).filter(email__in=emails)
        return users

    def get_user_received_users_count(self):
        users = self.pending_connections.filter(request=True, send_request="Process")
        emails = [user.connection_user.email for user in users]
        users = User.objects.exclude(email=self.email).filter(email__in=emails).count()
        return users

    def get_remaining_users(self):
        emails = [user.connection_user.email for user in self.connections.filter(send_request="Accepted")]
        pending_emails = [user.connection_user.email for user in
                          self.pending_connections.filter(send_request="Accepted")]
        emails = emails + pending_emails
        users = User.objects.exclude(email=self.email).exclude(email__in=emails)
        return users

    def get_profile_img(self):
        if self.is_college_user_profile():
            return self.get_college_obj().get_profile_img()
        elif self.is_industry_user_profile():
            return self.get_industry_obj().get_profile_img()
        if self.profile_image:
            return self.profile_image.url
        else:
            return '/static/images/icon/user.png'

    def get_cover_img(self):
        if self.is_college_user_profile():
            return self.get_college_obj().get_cover_img()
        elif self.is_industry_user_profile():
            return self.get_industry_obj().get_cover_img()
        if self.cover_image:
            return self.cover_image.url
        else:
            return '/static/images/icon/user.png'

    def get_user_about_me(self):
        if self.is_college_user_profile():
            if self.get_college_obj().about_us:
                return self.get_college_obj().about_us
            else:
                return 'N.A.'
        if self.is_industry_user_profile():
            if self.get_industry_obj().about_us:
                return self.get_industry_obj().about_us
            else:
                return 'N.A.'
        user_info = self.user_basic
        if user_info and user_info.about_me:
            return user_info.about_me
        return 'N.A.'

    def get_user_city(self):
        if self.is_industry_user_profile():
            if self.get_industry_obj().headquarters:
                return self.get_industry_obj().headquarters
            else:
                return 'N.A.'
        user_info = self.user_basic
        if user_info and user_info.city:
            return user_info.city
        return 'N.A.'

    def get_user_dob(self):
        user_info = self.user_basic
        if user_info and user_info.dob:
            return user_info.dob.strftime("%d %b, %Y")
        return 'N.A.'

    def get_college_name(self):
        if self.is_college_user_profile():
            if self.get_college_obj().name:
                return self.get_college_obj().name
            else:
                return 'N.A.'
        user_education = self.education
        if user_education and user_education.college.name:
            return user_education.college.name
        return 'N.A.'

    def get_college_current_status(self):
        user_education = self.education
        if user_education and user_education.current_status:
            return user_education.current_status
        return 'N.A.'

    def get_college_year(self):
        user_education = self.education
        if user_education and user_education.admission_year and user_education.passout_year:
            return f"{user_education.admission_year}-{user_education.passout_year}"
        return 'N.A.'

    def get_college_branch(self):
        user_education = self.education
        if user_education and user_education.branch:
            return f"{user_education.branch}"
        return 'N.A.'

    def get_user_interest(self):
        a = self.user_interest
        if not a:
            return []
        # a = UserInterest.objects.filter(user=self).last()
        if a.interest.all():
            return a.interest.all()
        return []

    def get_user_groups(self):
        groups = self.groups.all()
        return groups

    def is_college_user_true(self, college_id):
        user_education = UserEducation.objects.filter(user=self, college__id=college_id).last()
        if user_education:
            return True
        return False

    def is_college_user(self):
        return self.user_type == 'college' and self.is_verified and self.is_active

    def is_college_user_profile(self):
        return self.user_type == 'college' and self.is_active

    def is_industry_user(self):
        return self.user_type == 'industry' and self.is_verified and self.is_active

    def is_industry_user_profile(self):
        return self.user_type == 'industry' and self.is_active

    def get_company_name(self):
        if self.is_industry_user_profile():
            return self.get_industry_obj().name

    def get_college_obj(self):
        return CollegeName.objects.filter(college_users__in=[self]).last()

    def get_industry_obj(self):
        return Company.objects.filter(user=self).last()

    def get_user_education(self):
        education = UserEducation.objects.filter(user=self).last()
        return education

    def get_uploaded_document(self):
        if self.uploaded_document:
            return self.uploaded_document.url
        return ''


class Connection(models.Model):
    connection_user = models.ForeignKey(User, on_delete=models.CASCADE)
    request = models.BooleanField(default=False)
    send_request = models.CharField(max_length=10, choices=REQUEST_CHOICES, default='Process')

    def __str__(self):
        return self.connection_user.username
