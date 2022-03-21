from django.urls import path
from . import views

app_name = 'industry'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/users/', views.SearchResult.as_view(), name='search'),

]