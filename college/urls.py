from django.urls import path
from . import views


app_name = 'college'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('info/<int:pk>/', views.CollegeInfoView.as_view(), name='info'),
    path('user/list/',views.CollegeUserList.as_view(), name='user-list'),
    path('user/detail/<int:pk>/', views.CollegeUserDetailView.as_view(), name='user-detail'),
    path('delete/branch/', views.DeleteBranch.as_view(), name='delete-branch'),
]