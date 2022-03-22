import django_filters
from django import forms
from django.db.models import Q

from users.models import User


class UserFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    birth_year = django_filters.CharFilter(method='dob_check')
    username = django_filters.CharFilter(field_name='username', lookup_expr='iexact')
    status = django_filters.CharFilter(method='status_check')
    branch = django_filters.CharFilter(field_name='education__branch', lookup_expr='iexact')
    admission_year = django_filters.CharFilter(field_name='education__admission_year', lookup_expr='iexact')
    passout_year = django_filters.CharFilter(field_name='education__passout_year', lookup_expr='iexact')
    company = django_filters.CharFilter(field_name='education__current_company__name')
    phone_number = django_filters.CharFilter(field_name='phone_number', lookup_expr='iexact')
    user_type = django_filters.CharFilter(method='check_usertype')

    def check_usertype(self, queryset, value, *args, **kwargs):
        try:
            value = args[0]
            if not value:
                return queryset
            if value == "student":
                return queryset.filter(user_type ='student')
            elif value == "college":
                return queryset.filter(user_type='college')
            elif value == "industry":
                return queryset.filter(user_type='industry')
            return queryset
        except:
            return queryset

    def status_check(self, queryset, value, *args, **kwargs):
        try:
            value = args[0]
            if not value:
                return queryset
            if value == "active":
                return queryset.filter(is_verified=True)
            elif value == "unapproved":
                return queryset.filter(is_verified=False)
            elif value == "decline":
                return queryset.filter(is_declined=True)
            return queryset
        except:
            return queryset

    def dob_check(self, queryset, value, *args, **kwargs):
        try:
            value = args[0]
            if not value:
                return queryset
            return queryset.filter(
                Q(user_basic__dob__year=value))
        except:
            return queryset

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'branch', 'education', 'phone_number']
