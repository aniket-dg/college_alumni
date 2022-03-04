from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, FormView, UpdateView, DetailView

from users.forms import RegistrationForm, LoginForm, UserUpdateForm
from users.models import User, Connection


class UserProfileView(View):
    def get(self,*args, **kwargs):
        return HttpResponse("Profile VIew")



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
        user.is_active = True
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


class AcceptUserRequest(LoginRequiredMixin, View):
    def get(self,*args, **kwargs):
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

class SendUserRequest(LoginRequiredMixin, View):

    def get(self,*args, **kwargs):
        id = self.request.GET.get('id')
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
    template_name = 'users/profile.html'

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
