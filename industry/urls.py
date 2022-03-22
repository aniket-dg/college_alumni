from django.urls import path
from . import views

app_name = 'industry'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/users/', views.SearchResult.as_view(), name='search'),
    path('user/detail/<int:pk>/', views.IndustryUserDetailView.as_view(), name='user-detail'),
    path('info/<int:pk>/', views.IndustryInfoView.as_view(), name='info'),
    path('user/list/', views.IndustryUserList.as_view(), name='user-list'),

    path('generate/excel/', views.GenerateExcelToFilterUser.as_view(), name='generate-excel-list'),
    path('generate/pdf/', views.GeneratePdfToFilterUser.as_view(), name='generate-pdf-list'),
    path('send/sms/', views.SendSMSToFilterUser.as_view(), name='send-sms-user-list'),
    path('sample/', views.SampleView.as_view(), name='sample'),

]