from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from college import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('users.urls')),
    path('chat/', include('chat.urls')),
    path('post/', include('post.urls')),
    path('analytics/', include('analytics.urls')),
    path('college/', include('college.urls')),
    path('industry/', include('industry.urls')),
    re_path(r'^$', views.handler404),
    re_path(r'^$', views.handler500),

]
handler404 = 'college.views.handler404'
handler500 = 'college.views.handler500'
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)