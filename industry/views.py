import requests
import xlwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin, xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, UpdateView
from weasyprint import HTML

from college.filters import UserFilter
from industry.forms import CompanyForm
from industry.models import Company
from users.models import CollegeName, BranchName, User


class IsIndustryUser:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_industry_user():
            return super().dispatch(request, *args, **kwargs)
        elif request.user.is_superuser:
            return redirect('analytics:home')
        elif request.user.is_college_user():
            return redirect('college:home')
        messages.warning(request, "Unauthorized Access!")
        return redirect('profile')


class HomeView(LoginRequiredMixin, IsIndustryUser, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        # context['companies'] = Company.objects.all()
        context['colleges'] = CollegeName.objects.all()
        context['branches'] = BranchName.objects.all()
        context['industry_info'] = self.request.user.get_industry_obj()
        return render(self.request, 'industry/industry_home.html', context)


class SearchResult(LoginRequiredMixin, IsIndustryUser, ListView):
    model = User
    template_name = 'industry/search_result.html'

    # paginate_by = 1

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.filter(user_type='student', is_active=True,
                                       is_verified=True,
                                       is_declined=False)
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


@method_decorator(xframe_options_sameorigin, name='dispatch')
class IndustryUserDetailView(LoginRequiredMixin, IsIndustryUser, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'industry/college_user_detail.html'

    def test_func(self):
        return True

    def render_to_response(self, context, **response_kwargs):
        response = super(IndustryUserDetailView, self).render_to_response(context, **response_kwargs)
        return response

    @method_decorator(xframe_options_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(IndustryUserDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndustryUserDetailView, self).get_context_data(**kwargs)
        context['user_basic'] = self.get_object().user_basic
        context['user_education'] = self.get_object().education
        return context
    # def get_queryset(self):
    #     return is_college_student(self.request, self.object)


class IndustryInfoView(LoginRequiredMixin, IsIndustryUser, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'industry/industry_info.html'

    def get_context_data(self, **kwargs):
        context = super(IndustryInfoView, self).get_context_data(**kwargs)
        context['industry_info'] = self.get_object()
        return context

    def test_func(self):
        obj = self.get_object()
        if obj == self.request.user.get_industry_obj():
            return True
        return False

    def form_valid(self, form):
        print(self.request.POST)
        college = self.get_object()
        # college.branches.all().delete()
        college_form = form.instance

        college_form.save()
        messages.success(self.request, "Industry info saved successfully")
        return redirect('industry:info', pk=college_form.id)


class IndustryUserList(LoginRequiredMixin, IsIndustryUser, ListView):
    model = User
    template_name = 'industry/industry_user_list.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True,
                                       is_verified=True,
                                       user_type='student',
                                       is_declined=False
                                       )
        # print(college_user)
        # queryset = get_college_user(self.request)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(IndustryUserList, self).get_context_data(**kwargs)
        # print(self.object_list)
        context['table_title'] = "User List"
        context['table_sub_title'] = "Alumni Student"
        context['active_list'] = "approve_user_list"
        return context


class GenerateExcelToFilterUser(LoginRequiredMixin,  IsIndustryUser,UserPassesTestMixin, View):
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

        columns = ['First Name',
                   'Last Name',
                   # 'Email',
                   # 'Date of Birth',
                   # 'Phone Number',
                   'Branch',
                   'City',
                   'Admission Year',
                   'Passout Year',
                   'Current Status',
                   'Current City',
                   'Current Company'
                   ]
        object_list = []
        for item in user_list:
            user = []
            user.append(item.first_name)
            user.append(item.last_name)
            # user.append(item.email)
            # user.append(item.user_basic.dob if item.user_basic.dob else None)
            # user.append(item.phone_number if item.phone_number else None)
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
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_super_user:
            return True
        return False


@method_decorator(csrf_exempt, name='dispatch')
class GeneratePdfToFilterUser(LoginRequiredMixin, IsIndustryUser, UserPassesTestMixin, View):
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
        context['protected'] = True
        template = get_template('industry/generated_users_list.html')
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
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_super_user:
            return True
        return False


class SendSMSToFilterUser(LoginRequiredMixin, IsIndustryUser, UserPassesTestMixin, View):
    def post(self, *args, **kwargs):
        redirect_url = self.request.META.get('HTTP_REFERER')
        ids = self.request.POST.getlist('filter_list[]')
        message = self.request.POST.get('message')
        ids = list(set(ids))
        object_list = []
        for item in ids:
            user = User.objects.filter(id=int(item)).last()
            print(user)
            if user:
                object_list.append(user)
        send_sms_loop(self.request, message, object_list)
        messages.success(self.request, "Sending message to users!")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('industry:home')

    def test_func(self):
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_super_user:
            return True
        return False


def send_sms_loop(request, message, object_list):
    for object in object_list:
        print(object)
        if object.phone_number:
            send_sms(request, message, object.phone_number)


def send_sms(request, message, phone_number):
    url = "https://www.fast2sms.com/dev/bulkV2"
    print(message, "AniketGAvali")
    paylod = f"sender_id=TXTIND&message={message}&route=v3&numbers={phone_number}"
    headers = {
        'authorization': settings.FAST_SMS_API,
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
    }
    response = requests.request("POST", url, data=paylod, headers=headers)
    response = response.text
    if response[1] == 'true':
        return True

class SampleView(LoginRequiredMixin, IsIndustryUser, View):
    def get(self, *args, **kwargs):
        context = {}
        context['object_list'] = User.objects.all()
        return render(self.request, 'industry/generated_users_list.html', context)