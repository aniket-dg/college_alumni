from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, FormView, UpdateView, DetailView

from industry.models import Company
from post.models import Post, Category
from users.forms import RegistrationForm, LoginForm, UserUpdateForm, ProfilePhotoForm, CoverPhotoForm, UserNameForm, \
    UserBasicForm, UserEducationForm
from users.models import User, Connection, UserBasic, UserEducation, CollegeName, BranchName, UserInterest, Interest


class IsBasicInfoFill:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_info_save():
            return super().dispatch(request, *args, **kwargs)
        else:
            if not request.user.is_basic_info:
                messages.info(request, "Please fill basic info first.")
                return redirect('user:user-basic-info')
            elif not request.user.is_work_education:
                messages.info(request, "Specify Education and work information")
                return redirect('user:user-education')
            else:
                messages.info(request, "Please tell about your Interest.")
                return redirect('user:user-interest')


class IsUserActive:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_verified:
            return super().dispatch(request, *args, **kwargs)
        else:
            if request.user.is_basic_info and request.user.is_work_education and request.user.is_interest:
                messages.error(request, "Your account is not verified yet!")
            return redirect('user:profile')


class UserProfileView(IsBasicInfoFill, View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user
        context['post_list'] = Post.objects.filter(user=user)
        context['user'] = self.request.user
        context['profile_user'] = self.request.user
        connected_users = user.get_user_connected_users()
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
            return redirect('user:profile')
        context['post_list'] = Post.objects.filter(user=user)
        context['user'] = user
        context['profile_user'] = user
        connected_users = user.get_user_connected_users()
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
        return redirect('user:profile')

    def form_invalid(self, form):
        redirect_url = self.request.META.get('HTTP_REFERER')
        if redirect_url:
            return redirect(redirect_url)
        return redirect('user:profile')

    def test_func(self):
        model = self.get_object()
        return self.request.user == model


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = 'users/register.html'
    success_url = '/user/login/'
    form_class = RegistrationForm
    success_message = "Your account was created successfully"

    def form_valid(self, form):
        user = form.instance
        user.is_active = False
        user.is_verified = False
        user.save()
        user_type = self.request.POST.get('user_type')
        if user_type == "college":
            user.user_type = "college"
        elif user_type == "industry":
            user.user_type = "industry"
        else:
            user.user_type = "student"
        user.save()
        return super().form_valid(form)


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
            return redirect('user:login')

        if user is not None:
            if user.is_active:
                login(self.request, user)
                url_redirect = self.request.POST.get('redirect', None)
                if url_redirect:
                    return redirect(url_redirect)
                if self.request.GET.get('next'):
                    return redirect(self.request.GET.get('next'))
                return redirect('home:home')
            else:
                messages.warning(self.request,
                                 'Your account is not active, check your mail for activation link or contact support!')
                return redirect('user:login')

        if not user_query.is_active:
            messages.warning(self.request,
                             'Your account is not active, check your mail for activation link or contact support!')
            return redirect('user:login')
        else:
            messages.warning(self.request, 'Email or Password is incorrect')
            return redirect('user:login')


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
            # return redirect('user:profile')
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
        # return redirect('user:profile')
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
            # return redirect('user:profile')
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
        # return redirect('user:profile')
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
                'url': reverse('user:profile')
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
        # return redirect('user:profile')

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
                'url': reverse('user:profile')
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
        # return redirect('user:profile')
        return JsonResponse({
            'status': 'failure',
            'error': 'User not found.'
        })


class CheckProfile:
    def dispatch(self, request, *args, **kwargs):
        if request.user.id == self.kwargs.get('pk'):
            return redirect('user:profile')
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
            return redirect('user:profile')
        if user_friend not in user.get_user_connected_users():
            messages.warning(self.request, "User not found")
            if redirect_url:
                return redirect(redirect_url)
            return redirect('user:profile')
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
        return redirect('user:profile')


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
            return redirect('user:user-timeline')
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
            return redirect('user:user-groups')
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
            return redirect('user:user-education')
        if not self.request.user.is_interest:
            return redirect('user:user-interest')
        return redirect('user:profile')


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
                return redirect('user:user-interest')
            return redirect('user:user-education')

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
        return redirect('user:user-interest')


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
        return redirect('user:profile')


class CoverPhotoView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CoverPhotoForm

    def form_valid(self, form):
        print(self.request.POST)
        redirect_url = self.request.META.get('HTTP_REFERER')
        user = form.instance
        user.save()
        if redirect_url:
            return redirect(redirect_url)
        return redirect('user:profile')
