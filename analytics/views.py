import xlwt
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin, xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from weasyprint import HTML

from college.filters import UserFilter
from college.models import College
from college.views import send_sms_loop
from industry.models import Company
from users.models import User, BranchName, CollegeName
from users.views import make_friends


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
        context['unapproved_student'] = User.objects.filter(is_verified=False, user_type='student')[:5]
        context['unapproved_colleges'] = User.objects.filter(is_verified=False, user_type='college')[:5]
        context['unapproved_industry'] = User.objects.filter(is_verified=False, user_type='industry')[:5]
        context['colleges'] = College.objects.all()
        context['branches'] = BranchName.objects.all()
        return render(self.request, 'analytics/home.html', context)


class SearchResult(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/search_result.html'

    # paginate_by = 1

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.all().exclude(is_superuser=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SearchResult, self).get_context_data(**kwargs)
        filter_query = UserFilter(self.request.GET, self.object_list)
        print(filter_query.qs, len(filter_query.qs))
        if len(filter_query.qs) != len(self.object_list):
            context['object_list'] = filter_query.qs
            context['user_list'] = filter_query.qs
            # context['user_list'] = context['user_list'][self.paginate_by:]
            # if len(filter_query.qs) <= self.paginate_by:
            #     context['is_paginated'] = False
        return context


@method_decorator(xframe_options_sameorigin, name='dispatch')
class CollegeUserDetailView(LoginRequiredMixin, IsSuperAdmin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'analytics/college_user_detail.html'

    def test_func(self):
        return True

    def render_to_response(self, context, **response_kwargs):
        response = super(CollegeUserDetailView, self).render_to_response(context, **response_kwargs)
        return response

    @method_decorator(xframe_options_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CollegeUserDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CollegeUserDetailView, self).get_context_data(**kwargs)
        context['user_basic'] = self.get_object().user_basic
        context['user_education'] = self.get_object().education
        return context


class CollegeListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/college_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='college', is_verified=True, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CollegeListView, self).get_context_data(**kwargs)
        context['menu'] = "approve_college_list"

        return context


class UnApproveCollegeListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/college_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='college', is_verified=False, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UnApproveCollegeListView, self).get_context_data(**kwargs)
        context['menu'] = "unapprove_college_list"

        return context


class StudentListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/student_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='student', is_verified=True, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(StudentListView, self).get_context_data(**kwargs)
        context['menu'] = "approve_user_list"
        return context


class UnApproveStudentListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/student_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='student', is_verified=False, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UnApproveStudentListView, self).get_context_data(**kwargs)
        context['menu'] = "unapprove_user_list"
        return context


class IndustryListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/industry_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='industry', is_verified=True, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(IndustryListView, self).get_context_data(**kwargs)
        context['menu'] = "approve_industry_list"

        return context


class UnApproveIndustryListView(LoginRequiredMixin, IsSuperAdmin, ListView):
    model = User
    template_name = 'analytics/industry_list.html'
    paginate_by = 1

    def get_queryset(self):
        queryset = User.objects.filter(user_type='industry', is_verified=False, is_active=True)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UnApproveIndustryListView, self).get_context_data(**kwargs)
        context['menu'] = "unapprove_industry_list"

        return context


class CollegeDetailView(LoginRequiredMixin, IsSuperAdmin, DetailView):
    model = User
    template_name = 'analytics/college_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CollegeDetailView, self).get_context_data(**kwargs)
        context['college'] = CollegeName.objects.filter(college_users=self.get_object()).last()
        return context


class IndustryDetailView(LoginRequiredMixin, IsSuperAdmin, DetailView):
    model = User
    template_name = 'analytics/industry_detail.html'

    def get_context_data(self, **kwargs):
        context = super(IndustryDetailView, self).get_context_data(**kwargs)
        context['industry_info'] = Company.objects.filter(user=self.get_object()).last()
        return context


class UnapproveCollegeUser(LoginRequiredMixin, IsSuperAdmin, View):
    def post(self, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        reason = self.request.POST.get('reason_for_declined')
        redirect_url = self.request.META.get('HTTP_REFERER')

        if reason and len(reason.strip()) < 15:
            messages.info(self.request, "Sorry, please specify reason for declining user in more than 15 characters")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('analytics:user-detail', pk=self.kwargs.get('pk'))
        if not user:
            messages.warning(self.request, "User not found!")
            return redirect('analytics:user-detail', pk=self.kwargs.get('pk'))
        if not user.is_active:
            messages.info(self.request, "User not verified their account with registered email!")
            return redirect('analytics:user-detail', pk=self.kwargs.get('pk'))
        user.is_declined = True
        user.is_verified = False
        user.reason_for_declined = reason
        user.save()
        messages.success(self.request, "User deactivated successfully!")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('analytics:user-detail', pk=self.kwargs.get('pk'))


class ApproveCollegeUser(LoginRequiredMixin, IsSuperAdmin, View):
    def get(self, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        redirect_url = self.request.META.get('HTTP_REFERER')
        if not user:
            messages.warning(self.request, "User not found!")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('analytics:home')
        if not user.is_active:
            messages.info(self.request, "User not verified their account with registered email!")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('college:user-list')
        user.is_verified = True
        user.save()
        # make_friends(self.request.user, user)
        messages.success(self.request, "User account verified.")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('analytics:home')

class GenerateExcelToFilterUser(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, *args, **kwargs):

        ids = self.request.POST.getlist('filter_list[]')
        user_list = []
        for item in ids:
            user = User.objects.filter(id=int(item)).last()
            if user:
                user_list.append(user)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="users.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Users')

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['First Name', 'Last Name', 'Email', 'Date of Birth', 'Phone Number',
                   'Branch', 'City', 'Admission Year', 'Passout Year', 'Current Status',
                   'Current City', 'Current Company'
                   ]
        object_list = []
        for item in user_list:
            user = []
            user.append(item.first_name)
            user.append(item.last_name)
            user.append(item.email)
            user.append(item.user_basic.dob if item.user_basic.dob else None)
            user.append(item.phone_number if item.phone_number else None)
            user.append(item.education.branch if item.education.branch else None)
            user.append(item.user_basic.city if item.user_basic.city else None)
            user.append(item.education.admission_year if item.education.admission_year else None)
            user.append(item.education.passout_year if item.education.passout_year else None)
            user.append(item.education.current_status if item.education.current_status else None)
            user.append(item.education.current_city if item.education.current_city else None)
            user.append(item.education.current_company.name if item.education.current_company else None)

            object_list.append(user)

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        for member in object_list:
            row_num += 1
            for col_num in range(len(member)):
                ws.write(row_num, col_num, member[col_num], font_style)

        wb.save(response)
        return response

    def test_func(self):
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_superuser:
            return True
        return False



@method_decorator(csrf_exempt, name='dispatch')
class GeneratePdfToFilterUser(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, *args, **kwargs):
        ids = self.request.POST.getlist('filter_list[]')
        ids = list(set(ids))
        print(ids)
        object_list = []
        for item in ids:
            user = User.objects.filter(id=int(item)).last()
            if user:
                object_list.append(user)
        context = {}
        context['object_list'] = object_list
        template = get_template('college/generated_users_list.html')
        html = template.render({'object_list': object_list})
        # print(html)

        html = HTML(string=html, base_url=self.request.build_absolute_uri())
        a = html.write_pdf(stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css'],
                           presentational_hints=True)
        response = HttpResponse(a, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Users.pdf"'
        return response
        # return render(self.request, 'college/generated_users_list.html', context)

    def test_func(self):
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_superuser:
            return True
        return False


class SendSMSToFilterUser(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, *args, **kwargs):
        redirect_url = self.request.META.get('HTTP_REFERER')
        ids = self.request.POST.getlist('filter_list[]')
        message = self.request.POST.get('message')
        ids = list(set(ids))
        object_list = []
        for item in ids:
            user = User.objects.filter(id =int(item)).last()
            print(user)
            if user:
                object_list.append(user)
        send_sms_loop(self.request, message, object_list)
        messages.success(self.request, "Sending message to users!")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('college:home')

    def test_func(self):
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_superuser:
            return True
        return False