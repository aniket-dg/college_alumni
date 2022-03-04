from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'user'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('update/<int:pk>/', views.UserUpdateView.as_view(), name='update'),


# Password
    # Password Change
    path('change-password/', auth_views.PasswordChangeView.as_view(template_name='users/password_change.html'),
         name='password_change'),
    path('change-password-done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'),
         name='password_change_done'),

    # Forgot Password
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html',
                                                                 email_template_name='users/password_reset_email.html',
                                                                 success_url=reverse_lazy('user:password_reset_done'),
                                                                 from_email='info@stellar-ai.in'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html',
                                                     success_url=reverse_lazy('user:password_reset_complete')),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),


    path('accept/request/', views.AcceptUserRequest.as_view(), name='accept-user'),
    path('send/request/', views.SendUserRequest.as_view(), name='send-request'),
    path('profile/<int:pk>/', views.UserFriendProfileView.as_view(), name='friend-profile'),

]