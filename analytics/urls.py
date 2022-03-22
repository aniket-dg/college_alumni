from django.urls import path
from . import views
app_name = 'analytics'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/users/', views.SearchResult.as_view(), name='search'),
    path('student/list/', views.StudentListView.as_view(), name='student-list'),
    path('inactive/student/list/', views.UnApproveStudentListView.as_view(), name='inactive-student-list'),
    path('user/detail/<int:pk>/', views.CollegeUserDetailView.as_view(), name='user-detail'),

    path('industry/detail/<int:pk>/', views.IndustryDetailView.as_view(), name='industry-detail'),
    path('industry/list/', views.IndustryListView.as_view(), name='industry-list'),
    path('inactive/industry/list/', views.UnApproveIndustryListView.as_view(), name='inactive-industry-list'),

    path('college/list/', views.CollegeListView.as_view(), name='college-list'),
    path('inactive/college/list/', views.UnApproveCollegeListView.as_view(), name='inactive-college-list'),
    path('college/detail/<int:pk>/', views.CollegeDetailView.as_view(), name='college-detail'),

    path('disapprove/user/<int:pk>/', views.UnapproveCollegeUser.as_view(), name='disapprove-user'),
    path('approve/user/<int:pk>/', views.ApproveCollegeUser.as_view(), name='approve-user'),

    path('generate/excel/', views.GenerateExcelToFilterUser.as_view(), name='generate-excel-list'),
    path('generate/pdf/', views.GeneratePdfToFilterUser.as_view(), name='generate-pdf-list'),
    path('send/sms/', views.SendSMSToFilterUser.as_view(), name='send-sms-user-list'),


]