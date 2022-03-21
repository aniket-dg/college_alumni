from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect


# Create your views here.
from django.views import View
from django.views.generic import ListView

from college.filters import UserFilter
from industry.models import Company
from users.models import CollegeName, BranchName, User


class IsIndustryUser:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_college_user():
            return super().dispatch(request, *args, **kwargs)
        return redirect('post:post')


class HomeView(LoginRequiredMixin, IsIndustryUser, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['companies'] = Company.objects.all()
        context['colleges'] = CollegeName.objects.all()
        context['branches'] = BranchName.objects.all()
        return render(self.request, 'industry/industry_home.html', context)

class SearchResult(LoginRequiredMixin, IsIndustryUser, ListView):
    model = User
    template_name = 'industry/search_result.html'

    # paginate_by = 1

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.filter(user_type='student')
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SearchResult, self).get_context_data(**kwargs)
        print(self.request.GET)
        filter_query = UserFilter(self.request.GET, self.object_list)
        print(filter_query.qs, len(filter_query.qs))
        if len(filter_query.qs) != len(self.object_list):
            context['object_list'] = filter_query.qs
            context['user_list'] = filter_query.qs
            # context['user_list'] = context['user_list'][self.paginate_by:]
            # if len(filter_query.qs) <= self.paginate_by:
            #     context['is_paginated'] = False
        return context
