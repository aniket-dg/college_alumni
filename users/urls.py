from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

# app_name = 'user'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('', views.UserProfileView.as_view(), name='profile'),
    path('friend/list/<int:pk>/', views.UserUserFriendView.as_view(), name='user-user-friend'),
    path('update/<int:pk>/', views.UserUpdateView.as_view(), name='update'),
    path('resend-confirmation/', views.ResendMailConfirmationView.as_view(),
         name='resend-email-confirmation'),
    path('activate/<uidb64>/<token>', views.EmailVerificationView.as_view(), name='activate'),
    # Password
    # Password Change
    # path('change-password/', auth_views.PasswordChangeView.as_view(template_name='users/password_change.html'),
    #      name='password_change'),
    path('change-password-done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'),
         name='password_change_done'),

    # Forgot Password
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html',
                                                                 email_template_name='users/password_reset_email.html',
                                                                 success_url=reverse_lazy('password_reset_done'),
                                                                 from_email='info@stellar-ai.in'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html',
                                                     success_url=reverse_lazy('password_reset_complete')),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    path('accept/request/', views.AcceptUserRequest.as_view(), name='accept-user'),
    path('send/request/', views.SendUserRequest.as_view(), name='send-request'),
    path('profile/<int:pk>/', views.UserFriendProfileView.as_view(), name='friend-profile'),
    path('search/', views.UsersAndPostsSearchView.as_view(), name='search-user-post'),
    path('unfriend/user/<int:pk>/', views.UnfriendUser.as_view(), name='unfriend-user'),

    path('timeline/', views.UserTimeLineView.as_view(), name='user-timeline'),
    path('timeline/<int:pk>/', views.UserFriendTimeLineView.as_view(), name='user-friend-timeline'),
    path('groups/', views.UserGroupsView.as_view(), name='user-groups'),
    path('friend/groups/<int:pk>/', views.UserFriendGroupsView.as_view(), name='user-friend-groups'),

    path('basic/info/', views.UserBasicInfoView.as_view(), name='user-basic-info'),
    path('college/basic/info/<int:pk>/', views.CollegeBasicInfo.as_view(), name='college-basic-info'),
    path('industry/basic/info/<int:pk>/', views.IndustryBasicInfo.as_view(), name='industry-basic-info'),
    path('education/', views.UserEducationView.as_view(), name='user-education'),
    path('interest/', views.UserInterestView.as_view(), name='user-interest'),
    path('delete/interest/', views.RemoveInterest.as_view(), name='remove-interest'),
    path('add/interest/', views.AddInterest.as_view(), name='add-interest'),
    path('profile/photo/<int:pk>/', views.ProfilePhotoView.as_view(), name='user-profile-photo'),
    path('cover/photo/<int:pk>/', views.CoverPhotoView.as_view(), name='user-cover-photo'),


    path('college/profile/photo/<int:pk>/', views.CollegeProfilePhotoView.as_view(), name='college-profile-photo'),
    path('industry/profile/photo/<int:pk>/', views.IndustryProfilePhotoView.as_view(), name='industry-profile-photo'),
    path('college/cover/photo/<int:pk>/', views.CollegeCoverPhotoView.as_view(), name='college-cover-photo'),
    path('industry/cover/photo/<int:pk>/', views.IndustryCoverPhotoView.as_view(), name='industry-cover-photo'),

    path('sample/', views.SampleView.as_view(), name='sample'),
]
