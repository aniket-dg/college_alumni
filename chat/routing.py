# chat/routing.py
from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [

    path('ws/chat/p/<str:sender>/<str:receiver>/', consumers.P2pConsumer.as_asgi()),
    path('ws/chat/group/<str:group_name>/<str:sender>/', consumers.GroupConsumer.as_asgi()),

]