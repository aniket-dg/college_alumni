from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, FormView, UpdateView, DetailView

from college.forms import CollegeBasicInfoForm
from college.models import College
from industry.forms import CompanyForm, CompanyProfilePhotoForm, CompanyCoverPhotoForm
from industry.models import Company
from post.models import Post, Category
from users.forms import RegistrationForm, LoginForm, UserUpdateForm, ProfilePhotoForm, CoverPhotoForm, UserNameForm, \
    UserBasicForm, UserEducationForm, EmailForm, CollegeCoverPhotoForm, CollegeProfilePhotoForm
from users.models import User, Connection, UserBasic, UserEducation, CollegeName, BranchName, UserInterest, Interest
from users.utils import account_activation_token, send_activation_mail


class IsBasicInfoFill:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_info_save() or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        else:
            if not request.user.is_basic_info:
                messages.info(request, "Please fill basic info first.")
                return redirect('user-basic-info')
            if request.user.is_college_user_profile():
                return super().dispatch(request, *args, **kwargs)
            if request.user.is_industry_user_profile():
                return super().dispatch(request, *args, **kwargs)
            elif not request.user.is_work_education:
                messages.info(request, "Specify Education and work information")
                return redirect('user-education')
            else:
                messages.info(request, "Please tell about your Interest.")
                return redirect('user-interest')


class IsUserActive:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_verified:
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "Your account is not verified yet! Once verified, you will get notification on "
                                    "you registered mobile number")
            return redirect('profile')


class UserProfileView(IsBasicInfoFill, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['post_list'] = Post.objects.filter(user=user)
        context['user'] = self.request.user
        context['profile_user'] = self.request.user
        connected_users = user.get_user_connected_users_profile()
        print(connected_users, "Aniket")
        requested_users = user.get_user_requested_users()
        received_users = user.get_user_received_users()
        remaining_users = user.get_remaining_users()
        context['connected_users'] = connected_users
        context['requested_users'] = requested_users
        context['received_users'] = received_users
        context['remaining_users'] = remaining_users
        return render(self.request, 'users/profile.html', context)


class UserUserFriendView(IsBasicInfoFill, View):
    def get(self, *args, **kwargs):
        context = {}
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        if not user:
            messages.warning(self.request, "User not found")
            return redirect('profile')
        context['post_list'] = Post.objects.filter(user=user)
        context['user'] = user
        context['profile_user'] = user
        connected_users = user.get_user_connected_users_profile()
        requested_users = user.get_user_requested_users()
        received_users = user.get_user_received_users()
        remaining_users = user.get_remaining_users()
        context['connected_users'] = connected_users
        context['requested_users'] = requested_users
        context['received_users'] = received_users
        context['remaining_users'] = remaining_users
        return render(self.request, 'users/profile.html', context)


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone_number', 'bio', 'designation']
    template_name = 'users/profile.html'
    success_message = 'Profile successfully updated'

    def form_valid(self, form):
        user = form.instance
        user.save()

        redirect_url = self.request.META.get('HTTP_REFERER')
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def form_invalid(self, form):
        redirect_url = self.request.META.get('HTTP_REFERER')
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def test_func(self):
        model = self.get_object()
        return self.request.user == model


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = 'users/register.html'
    success_url = '/users/login/'
    form_class = RegistrationForm
    success_message = "Your account was created successfully"

    def get_context_data(self, **kwargs):
        context = super(SignUpView, self).get_context_data(**kwargs)
        context['signup_error'] = "true"
        return context

    def form_valid(self, form):
        user = form.instance
        user_type = self.request.POST.get('user_type')
        if user_type == "industry":
            user.user_type = "industry"
            # user.college_code = None
            user.save()
            message = 'Account successfully created Please click the link in your mail and login to active your ' \
                      'account. '
            send_activation_mail(self.request, message, user)
            return super().form_valid(form)

        college_code = self.request.POST.get('college_code')
        if not college_code:
            messages.warning(self.request, "Please specify College Code!")
            return redirect('register')
        college = College.objects.filter(code=college_code).last()
        if not college:
            messages.info(self.request, "College code not valid. If problem persist, contact to support!")
            return redirect('register')

        if user_type == "college":
            user.user_type = "college"

            email = user.email
            domain = email.split("@")[1]
            if domain not in college.domain:
                messages.warning(self.request, "Enter verifiable institute-issued email address")
                return redirect('register')
            user.college_code = college_code
            user.save()
        else:
            user.user_type = "student"
        # user.is_active = False
        # user.is_verified = False
        user.college_code = college_code
        user.save()
        user.save()
        message = 'Account successfully created Please click the link in your mail and login to active your account.'
        send_activation_mail(self.request, message, user)
        return super().form_valid(form)

    # def form_invalid(self, form):
    #     print(form.errors)
    #     return HttpResponse("Error")


# Login View
class LoginView(SuccessMessageMixin, FormView):
    form_class = LoginForm
    template_name = 'users/login.html'
    success_url = '/'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.GET.get('next'):
                return redirect(self.request.GET.get('next'))
            return redirect('post:post')
        context = {}
        context['form'] = self.get_form()
        return render(self.request, 'users/login.html', context)

    def form_valid(self, form):
        credentials = form.cleaned_data
        user = authenticate(email=credentials['email'],
                            password=credentials['password'])
        # Get the user
        try:
            user_query = User.objects.get(email=credentials['email'])
        except ObjectDoesNotExist:
            messages.warning(self.request, 'Email or Password is incorrect')
            return redirect('login')

        if user is not None:
            if user.is_active:
                login(self.request, user)
                url_redirect = self.request.POST.get('redirect', None)
                if url_redirect:
                    return redirect(url_redirect)
                if self.request.GET.get('next'):
                    return redirect(self.request.GET.get('next'))
                return redirect('post:post')
            else:
                messages.warning(self.request,
                                 'Your account is not active, check your mail for activation link or contact support!')
                return redirect('login')

        if not user_query.is_active:
            messages.warning(self.request,
                             'Your account is not active, check your mail for activation link or contact support!')
            return redirect('login')
        else:
            messages.warning(self.request, 'Email or Password is incorrect')
            return redirect('login')


# User logout view
class LogoutView(View):
    def get(self, *args, **kwargs):
        logout(self.request)
        self.request.session.flush()
        return redirect('/')


class AcceptUserRequest(LoginRequiredMixin, IsUserActive, View):
    def get(self, *args, **kwargs):
        redirect_url = self.request.META.get('HTTP_REFERER')
        id = self.request.GET.get('id')
        user = self.request.user
        request_user = User.objects.filter(id=int(id)).last()
        request_user_connection = request_user.connections.filter(connection_user=user).last()
        user_pending_connection = user.pending_connections.filter(connection_user=request_user).last()
        # print(request_user_connection, user_pending_connection)
        if request_user_connection and user_pending_connection:
            request_user_connection.send_request = "Accepted"
            request_user_connection.save()
            user_pending_connection.send_request = "Accepted"
            user_pending_connection.save()
            # messages.success(self.request, "Request accepted")
            # return redirect('profile')
            extra = {
                'title': 'Request accepted!',
                'url': reverse('chat:chat')
            }
            # save_notification_for_user(request_user, self.request.user)
            if redirect_url:
                messages.success(self.request, "Request Accepted!")
                return redirect(redirect_url)
            return JsonResponse({
                'status': 'success',
                'data': 'Request accepted!'
            })
        # messages.warning(self.request, "User not found")
        # return redirect('profile')
        if redirect_url:
            messages.warning(self.request, "You did not receive a request from this user.")
            return redirect(redirect_url)
        return JsonResponse({
            'status': 'failure',
            'error': 'You did not receive a request from this user.'
        })

    def post(self, *args, **kwargs):
        id = self.request.POST.get('id')
        user = self.request.user
        request_user = User.objects.filter(id=int(id)).last()
        request_user_connection = request_user.connections.filter(connection_user=user).last()
        user_pending_connection = user.pending_connections.filter(connection_user=request_user).last()
        # print(request_user_connection, user_pending_connection)
        if request_user_connection and user_pending_connection:
            request_user_connection.send_request = "Accepted"
            request_user_connection.save()
            user_pending_connection.send_request = "Accepted"
            user_pending_connection.save()
            # messages.success(self.request, "Request accepted")
            # return redirect('profile')
            extra = {
                'title': 'Request accepted!',
                'url': reverse('chat:chat')
            }
            # save_notification_for_user(request_user, self.request.user)
            return JsonResponse({
                'status': 'success',
                'data': 'Request accepted!'
            })
        # messages.warning(self.request, "User not found")
        # return redirect('profile')
        return JsonResponse({
            'status': 'failure',
            'error': 'You did not receive a request from this user.'
        })


def make_friends(sender, receiver):
    connection = Connection()
    connection.connection_user = sender
    connection.request = True
    connection.send_request = "Accepted"
    connection.save()
    connection = Connection()
    connection.connection_user = receiver
    connection.request = True
    connection.send_request = "Accepted"
    connection.save()


class SendUserRequest(LoginRequiredMixin, IsUserActive, View):
    def get(self, *args, **kwargs):
        id = self.request.GET.get('id')
        user = self.request.user
        redirect_url = self.request.META.get('HTTP_REFERER')
        send_request_user = User.objects.filter(id=int(id)).last()
        is_connection = send_request_user.pending_connections.filter(connection_user=user).exists()
        if send_request_user and not is_connection:
            connection = Connection()
            connection.connection_user = send_request_user
            connection.request = True
            connection.save()
            receive_connection = Connection()
            receive_connection.connection_user = user
            receive_connection.request = True
            receive_connection.save()
            user.connections.add(connection)
            send_request_user.pending_connections.add(receive_connection)
            send_request_user.save()
            user.save()
            extra = {
                'title': 'New friend request!',
                'url': reverse('profile')
                # 'icon': self.request.build_absolute_uri(user.get_profile_img()),
            }
            if redirect_url:
                messages.success(self.request, "Friend Request sent!")
                return redirect(redirect_url)
            return JsonResponse({
                'status': 'success',
                'data': 'Friend Request Sent!'
            })
        if redirect_url:
            messages.warning(self.request, "Already Requested")
            return redirect(redirect_url)
        if is_connection:
            return JsonResponse({
                'status': 'failure',
                'data': 'Already requested'
            })
        # messages.warning(self.request, "User not found")
        # return redirect('profile')

        if redirect_url:
            messages.warning(self.request, "User not found")
            return redirect(redirect_url)
        return JsonResponse({
            'status': 'failure',
            'error': 'User not found.'
        })

    def post(self, *args, **kwargs):
        id = self.request.POST.get('id')
        user = self.request.user
        send_request_user = User.objects.filter(id=int(id)).last()
        is_connection = send_request_user.pending_connections.filter(connection_user=user).exists()
        if send_request_user and not is_connection:
            connection = Connection()
            connection.connection_user = send_request_user
            connection.request = True
            connection.save()
            receive_connection = Connection()
            receive_connection.connection_user = user
            receive_connection.request = True
            receive_connection.save()
            user.connections.add(connection)
            send_request_user.pending_connections.add(receive_connection)
            send_request_user.save()
            user.save()
            extra = {
                'title': 'New friend request!',
                'url': reverse('profile')
                # 'icon': self.request.build_absolute_uri(user.get_profile_img()),
            }
            return JsonResponse({
                'status': 'success',
                'data': 'Friend Request Sent!'
            })
        if is_connection:
            return JsonResponse({
                'status': 'failure',
                'data': 'Already requested'
            })
        # messages.warning(self.request, "User not found")
        # return redirect('profile')
        return JsonResponse({
            'status': 'failure',
            'error': 'User not found.'
        })


class CheckProfile:
    def dispatch(self, request, *args, **kwargs):
        if request.user.id == self.kwargs.get('pk'):
            return redirect('profile')
        return super().dispatch(request, *args, **kwargs)


class UserFriendProfileView(LoginRequiredMixin, CheckProfile, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'users/friend_profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserFriendProfileView, self).get_context_data(**kwargs)
        user = self.get_object()

        context['user_friend'] = True
        # context['post_list'] = Post.objects.filter(user=user)
        context['profile_user'] = user
        context['form'] = UserUpdateForm(instance=user)
        connected_users = user.get_user_connected_users()
        context['connected_users'] = connected_users
        context['request_already_sent'] = user.pending_connections.filter(connection_user=self.request.user).exists()
        return context

    def test_func(self):
        return True


class UsersAndPostsSearchView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        query = self.request.GET.get('query')
        current_user = self.request.user
        user_list = []
        post_list = []
        users = User.objects.filter(Q(first_name__icontains=query) |
                                    Q(last_name__icontains=query) |
                                    Q(username__icontains=query))
        for user in users:
            # 0 -> Not Friend, 1 -> Already sent request, 2 -> Already Friend
            is_friend = 0
            if user.pending_connections.filter(connection_user=current_user).exists():
                is_friend = 1
            elif current_user.get_user_connected_users().filter(id=user.id).exists() or user == current_user:
                is_friend = 2
            user_list.append({
                'id': user.id,
                'name': user.get_full_name(),
                'username': user.username,
                'profile_image_url': user.get_profile_img(),
                'is_friend': is_friend
            })

        return JsonResponse({
            'user_list': user_list,
        })


class UnfriendUser(View):
    def get(self, *args, **kwargs):
        redirect_url = self.request.META.get('HTTP_REFERER')
        user_friend_id = self.kwargs.get('pk')
        user_friend = User.objects.filter(id=user_friend_id).last()
        user = self.request.user
        if not user_friend:
            messages.warning(self.request, "User not found")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('profile')
        if user_friend not in user.get_user_connected_users():
            messages.warning(self.request, "User not found")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('profile')
        if user_friend in user.get_user_connected_users() or user in user_friend.get_user_connected_users():
            user.connections.remove(*user.connections.filter(connection_user=user_friend))
            user.pending_connections.remove(*user.pending_connections.filter(connection_user=user_friend))
            user_friend.connections.remove(*user_friend.connections.filter(connection_user=user))
            user_friend.pending_connections.remove(*user_friend.pending_connections.filter(connection_user=user))

            user.save()
            user_friend.save()
        messages.success(self.request, "User removed from your friend list")
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')


class UserTimeLineView(LoginRequiredMixin, IsUserActive, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['category'] = Category.objects.all()
        context['user'] = user
        context['profile_user'] = user
        return render(self.request, "users/timeline.html", context)


class UserFriendTimeLineView(LoginRequiredMixin, IsUserActive, View):
    def get(self, *args, **kwargs):
        context = {}
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        if not user:
            messages.warning(self.request, "User not found")
            return redirect('user-timeline')
        context['category'] = Category.objects.all()
        context['user'] = user
        context['profile_user'] = user
        return render(self.request, "users/timeline.html", context)


class UserGroupsView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['profile_user'] = user
        context['user'] = self.request.user
        return render(self.request, "users/groups.html", context)


class UserFriendGroupsView(LoginRequiredMixin, CheckProfile, View):
    def get(self, *args, **kwargs):
        context = {}
        user = User.objects.filter(id=self.kwargs.get('pk')).last()
        if not user:
            return redirect('user-groups')
        context['profile_user'] = user
        return render(self.request, "users/groups.html", context)


class UserBasicInfoView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['user'] = user
        context['profile_user'] = user
        context['basic_info_present'] = user.user_basic
        context['basic_info'] = user.user_basic
        return render(self.request, "users/basic_info.html", context)

    def post(self, *args, **kwargs):
        context = {}
        print("Aniket here/////////////////")
        user_instance = UserNameForm(self.request.POST, instance=self.request.user)
        user_basic_form = UserBasicForm(self.request.POST)
        error = False
        if not user_instance.is_valid():
            error = True
            context['user_instance_error'] = user_instance
        if not user_basic_form.is_valid():
            error = True
            context['user_basic_error'] = user_basic_form
        if error:
            return render(self.request, 'users/basic_info.html', context)

        if user_instance.is_valid():
            user_instance.save()
        user_basic_form = UserBasicForm(self.request.POST)
        print(user_basic_form)
        user_basic = UserBasic.objects.filter(user=self.request.user).last()
        if user_basic_form.is_valid():
            if user_basic:
                user_basic.delete()
            user_basic = user_basic_form.instance
            user_basic.save()
            self.request.user.user_basic = user_basic
            self.request.user.save()
            # user_basic.user = self.request.user
            user_basic.about_me = user_basic.about_me.strip()
            user_basic.save()
            self.request.user.is_basic_info = True
            self.request.user.save()

        messages.success(self.request, "User info updated")
        if not self.request.user.is_work_education:
            return redirect('user-education')
        if not self.request.user.is_interest:
            return redirect('user-interest')
        return redirect('profile')


class CollegeBasicInfo(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = CollegeName
    form_class = CollegeBasicInfoForm

    def form_valid(self, form):
        college_info = form.instance
        college_info.save()
        self.request.user.is_basic_info = True
        self.request.user.save()
        messages.success(self.request, "College Info updated")
        redirect_url = self.request.META.get('HTTP_REFERER')
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def form_invalid(self, form):
        context = {}
        context['form'] = form
        return render(self.request, 'users/basic_info.html', context)

    def test_func(self):
        return self.get_object() == self.request.user.get_college_obj()

class IndustryBasicInfo(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = Company
    form_class = CompanyForm

    def form_valid(self, form):
        college_info = form.instance
        college_info.save()
        self.request.user.is_basic_info = True
        self.request.user.save()
        messages.success(self.request, "Industry Info updated")
        redirect_url = self.request.META.get('HTTP_REFERER')
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def form_invalid(self, form):
        context = {}
        context['form'] = form
        return render(self.request, 'users/basic_info.html', context)

    def test_func(self):
        return self.get_object() == self.request.user.get_industry_obj()

class UserEducationView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['user'] = user
        context['profile_user'] = user
        context['education_present'] = self.request.user.education
        context['education_info'] = self.request.user.education
        context['colleges'] = CollegeName.objects.all()
        context['branches'] = BranchName.objects.all()
        context['companies'] = Company.objects.all()
        return render(self.request, "users/education_work.html", context)

    def post(self, *args, **kwargs):
        print(self.request.POST)
        context = {}
        user = self.request.user
        print(self.request.POST)
        user_education = UserEducationForm(self.request.POST)
        if user_education.is_valid():
            print(user_education)
            education = user_education.instance
            education.save()
            self.request.user.education = education
            self.request.user.save()
            education.save()
            user.is_work_education = True
            user.save()
            messages.success(self.request, "Education and work info saved successfully!")
            if not user.is_interest:
                messages.info(self.request, "Please specify about your interest")
                return redirect('user-interest')
            return redirect('user-education')

        context['error'] = True
        context['education_error'] = user_education
        context['education_present'] = self.request.user.education
        context['education_info'] = self.request.user.education
        context['colleges'] = CollegeName.objects.all()
        context['branches'] = BranchName.objects.all()
        context['companies'] = Company.objects.all()
        return render(self.request, "users/education_work.html", context)


class UserInterestView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['profile_user'] = user
        context['interest_present'] = self.request.user.user_interest
        return render(self.request, 'users/interest.html', context)

    def post(self, *args, **kwargs):
        print(self.request.POST)
        # interest_list = self.request.POST.getlist('interest[]')
        #
        # user_interest = UserInterest.objects.filter(user=self.request.user).last()
        # if user_interest:
        #    user_interest.interest.all().delete()
        # if not user_interest:
        #     user_interest = UserInterest(user=self.request.user)
        # user_interest.save()
        # print(interest_list, "Aniket")
        # for item in interest_list:
        #     interest = Interest(name=item)
        #     interest.save()
        #     user_interest.interest.add(interest)
        #     user_interest.save()
        #     self.request.user.is_interest = True
        #     self.request.user.save()
        messages.success(self.request, "User interest saved!")
        return redirect('user-interest')


class RemoveInterest(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        name = self.request.GET.get('name')
        user_interest = self.request.user.user_interest
        if not user_interest:
            return JsonResponse({
                'error': "User Interest not found!"
            })
        is_interest = user_interest.interest.filter(name=name).last()
        if is_interest:
            is_interest.delete()
            user_interest.save()
            return JsonResponse({
                'data': "Interest deleted"
            })
        return JsonResponse({
            'error': "Interest not found!"
        })


class AddInterest(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        name = self.request.GET.get('name')
        user_interest = self.request.user.user_interest
        if not user_interest:
            user_interest = UserInterest()
            user_interest.save()
            self.request.user.user_interest = user_interest
            self.request.user.save()
        is_interest = user_interest.interest.filter(name=name).last()
        if is_interest:
            return JsonResponse({
                'data': "Interest added"
            })
        interest = Interest(name=name)
        interest.save()
        user_interest.interest.add(interest)
        user_interest.save()
        self.request.user.is_interest = True
        self.request.user.save()
        return JsonResponse({
            'error': "Interest added!"
        })


class ProfilePhotoView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfilePhotoForm

    def form_valid(self, form):
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')


class CollegeProfilePhotoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CollegeName
    form_class = CollegeProfilePhotoForm

    def form_valid(self, form):
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def test_func(self):
        return self.get_object() == self.request.user.get_college_obj()

class IndustryProfilePhotoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyProfilePhotoForm

    def form_valid(self, form):
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def test_func(self):
        return self.get_object() == self.request.user.get_industry_obj()


class CoverPhotoView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CoverPhotoForm

    def form_valid(self, form):
        user = self.request.user
        print(self.request.POST)
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')


class CollegeCoverPhotoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CollegeName
    form_class = CollegeCoverPhotoForm

    def form_valid(self, form):
        user = self.request.user
        print(self.request.POST)
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def test_func(self):
        return self.get_object() == self.request.user.get_college_obj()

class IndustryCoverPhotoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyCoverPhotoForm

    def form_valid(self, form):
        user = self.request.user
        print(self.request.POST)
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('profile')

    def test_func(self):
        return self.get_object() == self.request.user.get_industry_obj()


# Verifying email on link click
class EmailVerificationView(View):
    def get(self, request, uidb64, token):
        try:
            pk = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=pk)

            if not account_activation_token.check_token(user, token):
                return redirect('login' + '?message=' + 'User already activated')

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()

            if user.user_type == "college":
                college = College.objects.filter(code=user.college_code).last()
                if college:
                    a = CollegeName(name=college.name)
                    a.college_users = user
                    a.save()

            if user.user_type == "industry":
                industry = Company()
                industry.save()
                industry.user = user
                industry.save()
            messages.success(request, 'Account activated successfully')
            return redirect('login')

        except Exception as ex:
            pass

        return redirect('login')


# Resend Mail
class ResendMailConfirmationView(SuccessMessageMixin, FormView):
    form_class = EmailForm
    template_name = 'users/resend_mail.html'
    success_url = '/'

    def form_valid(self, form):
        # Get the user
        credentials = form.cleaned_data
        try:
            user = User.objects.get(email=credentials['email'])
        except ObjectDoesNotExist:
            messages.warning(self.request, 'Email is not correct')
            return redirect('resend-email-confirmation')

        # Check if user is active and send mail
        now = datetime.now()
        before_10_min = now + timedelta(minutes=-10)
        if not user.is_active:
            if user.date_confirmation_mail_sent > before_10_min:
                message = \
                    'Verification mail was just sent few minutes ago please check you mail or wait to resend again'
                messages.warning(self.request, message)
                return redirect('resend-email-confirmation')
            message = 'Verification Mail Resend!, Please click the link in your mail and login to active \
                       your account.'
            user.date_confirmation_mail_sent = now
            user.save()
            send_activation_mail(self.request, message, user)
            messages.success(self.request, 'Verification mail sent successfully')
            return redirect('login')
        else:
            messages.info(self.request, 'User is already active. Please Login!')
            return redirect('login')


class SampleView(View):
    def get(self, request):
        user = User.objects.get(email='royalaniket2512@gmail.com')
        send_activation_mail(request, "Sample message",user)
        return HttpResponse("Email sent")
        message = "Sample email"
        current_site = get_current_site(request)
        email_body = {
            # 'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        }

        link = reverse('activate', kwargs={'uidb64': email_body['uid'], 'token': email_body['token']})

        activate_url = 'http://' + current_site.domain + link

        email_subject = 'Welcome to '
        email_body_message = 'Please click the link and login to active your account'
        email_body = 'Hi ' + user.get_full_name() + ', ' + email_body_message + '. \n\n <a href=' + \
                     activate_url + '>activate</a>'

        email = EmailMessage(
            email_subject,
            email_body,
            settings.AUTH_USER_MODEL,
            [user.email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        messages.success(request, message)
