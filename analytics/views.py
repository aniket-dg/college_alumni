from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

# Create your views here.
from django.views import View

from users.models import User


class IsSuperAdmin:
    def dispatch(self, request, *args, **kwargs):
        context = {}
        user = request.user
        if user.is_active and user.is_verified and user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class HomeView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        unapproved_student = User.objects.filter(is_verified=False, user_type='student')[:5]
        unapproved_colleges = User.objects.filter(is_verified=False, user_type='college')[:5]
        unapproved_industry = User.objects.filter(is_verified=False, user_type='industry')[:5]

        return render(self.request, 'analytics/home.html')

