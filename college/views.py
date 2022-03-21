import xlwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
import requests
# Create your views here.
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, DeleteView, UpdateView
from weasyprint import HTML

from college.filters import UserFilter
from college.forms import CollegeForm
from college.models import College
from college.utils import get_college_user, is_college_student, get_college_all_users
from industry.models import Company
from users.models import BranchName, User, UserEducation, CollegeName, UserBasic
from users.views import make_friends


class IsCollegeUser:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_college_user():
            return super().dispatch(request, *args, **kwargs)
        return redirect('post:post')


class HomeView(LoginRequiredMixin, IsCollegeUser, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['branches'] = BranchName.objects.all()
        context['companies'] = Company.objects.all()
        return render(self.request, 'college/college_home.html', context)


class CollegeInfoView(LoginRequiredMixin, IsCollegeUser, UpdateView):
    model = CollegeName
    form_class = CollegeForm
    template_name = 'college/college_info.html'

    def get_context_data(self, **kwargs):
        context = super(CollegeInfoView, self).get_context_data(**kwargs)
        context['college_info'] = self.get_object()
        return context

    def form_valid(self, form):
        print(self.request.POST)
        college = self.get_object()
        # college.branches.all().delete()
        college_form = form.instance

        college_form.save()

        branch_list = self.request.POST.getlist('branches[]')
        for item in branch_list:
            print(item)
            branch = BranchName.objects.filter(name=item).last()
            if branch:
                college_form.branches.add(branch)
                college_form.save()
            branch = BranchName(name=item)
            branch.save()
            college_form.branches.add(branch)
            college_form.save()
        messages.success(self.request, "College info saved successfully")
        return redirect('college:info', pk=college_form.id)


class CollegeApproveUserList(LoginRequiredMixin, IsCollegeUser, ListView):
    model = User
    template_name = 'college/college_user_list.html'
    paginate_by = 2

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.filter(education__college=college, is_active=True,
                                       is_verified=False,
                                       user_type='student',
                                       is_declined=False)
        # print(college_user)
        # queryset = get_college_user(self.request)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CollegeApproveUserList, self).get_context_data(**kwargs)
        # print(self.object_list)
        # context['user_list'] = self.object_list
        context['table_title'] = "Unapproved Users"
        context['table_sub_title'] = "Unapproved Alumni Student"
        context['active_list'] = "unapprove_user_list"
        return context


class CollegeUserList(LoginRequiredMixin, IsCollegeUser, ListView):
    model = User
    template_name = 'college/college_user_list.html'
    paginate_by = 2

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.filter(education__college=college, is_active=True,
                                       is_verified=True,
                                       user_type='student',
                                       is_declined=False
                                       )
        # print(college_user)
        # queryset = get_college_user(self.request)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CollegeUserList, self).get_context_data(**kwargs)
        # print(self.object_list)
        context['table_title'] = "User List"
        context['table_sub_title'] = "Alumni Student"
        context['active_list'] = "approve_user_list"
        return context


@method_decorator(xframe_options_sameorigin, name='dispatch')
class CollegeUserDetailView(LoginRequiredMixin, IsCollegeUser, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'college/college_user_detail.html'

    def test_func(self):
        return is_college_student(self.request, self.get_object())

    def render_to_response(self, context, **response_kwargs):
        response = super(CollegeUserDetailView, self).render_to_response(context, **response_kwargs)
        return response

    @method_decorator(xframe_options_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CollegeUserDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CollegeUserDetailView, self).get_context_data(**kwargs)
        context['user_basic'] = UserBasic.objects.filter(user=self.get_object()).last()
        context['user_education'] = UserEducation.objects.filter(user=self.get_object()).last()
        return context
    # def get_queryset(self):
    #     return is_college_student(self.request, self.object)


class CollegeUserDeleteView(LoginRequiredMixin, IsCollegeUser, DeleteView):
    model = User

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        messages.info(self.request, "User deleted successfully")
        return redirect('college:home')


class ApproveCollegeUser(LoginRequiredMixin, IsCollegeUser, View):
    def get(self, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        redirect_url = self.request.META.get('HTTP_REFERER')
        if not user:
            messages.warning(self.request, "Alumni Student not found!")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('college:user-list')
        if not user.is_active:
            messages.info(self.request, "Alumni student not verified their account with registered email!")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('college:user-list')
        if is_college_student(self.request, user):
            user.is_verified = True
            user.save()
            make_friends(self.request.user, user)
            messages.success(self.request, "Student account verified.")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('college:user-list')
        messages.warning(self.request, "Alumni student isn't student of our institution")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('college:user-list')


class UnapproveCollegeUser(LoginRequiredMixin, IsCollegeUser, View):
    def post(self, *args, **kwargs):
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        reason = self.request.POST.get('reason_for_declined')
        redirect_url = self.request.META.get('HTTP_REFERER')

        if reason and len(reason.strip()) < 15:
            messages.info(self.request, "Sorry, please specify reason for declining user in more than 15 characters")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('college:user-detail', pk=self.kwargs.get('pk'))
        if not user:
            messages.warning(self.request, "Alumni Student not found!")
            return redirect('college:user-detail', pk=self.kwargs.get('pk'))
        if not user.is_active:
            messages.info(self.request, "Alumni student not verified their account with registered email!")
            return redirect('college:user-detail', pk=self.kwargs.get('pk'))
        if is_college_student(self.request, user):
            user.is_declined = True
            user.reason_for_declined = reason
            user.save()
            messages.success(self.request, "User deactivated successfully!")
            return redirect('college:user-detail', pk=self.kwargs.get('pk'))
        messages.warning(self.request, "Alumni student isn't student of our institution")
        return redirect('college:user-detail', pk=self.kwargs.get('pk'))


class DeleteBranch(LoginRequiredMixin, IsCollegeUser, View):
    def get(self, *args, **kwargs):
        print(self.request.GET)
        id = self.request.GET.get('name')
        branch = BranchName.objects.filter(name=id).last()
        if branch:
            branch.delete()
            return JsonResponse({
                'data': "Branch deleted!"
            })
        return JsonResponse({
            'error': "Branch not found!"
        })


class SearchResult(LoginRequiredMixin, IsCollegeUser, ListView):
    model = User
    template_name = 'college/search_result.html'

    # paginate_by = 1

    def get_queryset(self):
        college = self.request.user.get_college_obj()
        queryset = User.objects.filter(education__college=college)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SearchResult, self).get_context_data(**kwargs)
        print(self.request.GET)
        print(self.request.GET.get('first_name'))
        filter_query = UserFilter(self.request.GET, self.object_list)
        print(filter_query.qs, len(filter_query.qs))
        if len(filter_query.qs) != len(self.object_list):
            context['object_list'] = filter_query.qs
            context['user_list'] = filter_query.qs
            # context['user_list'] = context['user_list'][self.paginate_by:]
            # if len(filter_query.qs) <= self.paginate_by:
            #     context['is_paginated'] = False
        return context


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
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_super_user:
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
        if self.request.user.is_college_user() or self.request.user.is_industry_user() or self.request.user.is_super_user:
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
