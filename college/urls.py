from django.urls import path
from . import views

app_name = 'college'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('info/<int:pk>/', views.CollegeInfoView.as_view(), name='info'),
    path('approve/user/list/', views.CollegeApproveUserList.as_view(), name='unapprove-user-list'),
    path('user/list/', views.CollegeUserList.as_view(), name='user-list'),
    path('user/detail/<int:pk>/', views.CollegeUserDetailView.as_view(), name='user-detail'),
    path('delete/branch/', views.DeleteBranch.as_view(), name='delete-branch'),
    path('approve/user/<int:pk>/', views.ApproveCollegeUser.as_view(), name='approve-user'),
    path('disapprove/user/<int:pk>/', views.UnapproveCollegeUser.as_view(), name='disapprove-user'),
    path('search/users/', views.SearchResult.as_view(), name='search'),
    path('generate/excel/', views.GenerateExcelToFilterUser.as_view(), name='generate-excel-list'),
    path('generate/pdf/', views.GeneratePdfToFilterUser.as_view(), name='generate-pdf-list'),
    path('send/sms/', views.SendSMSToFilterUser.as_view(), name='send-sms-user-list'),

]
