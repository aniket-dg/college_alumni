from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api
app_name = 'chat'

router = DefaultRouter()
router.register(r'msg', api.P2pChatModelViewSet, basename='message-api')
router.register(r'group/msg', api.GroupChatModelViewSet, basename='group-message-api')

urlpatterns = [
    path('', views.HomeView.as_view(), name='chat'),
    path('group/update/', views.GroupUpdateView.as_view(), name='group-update'),
    path('group/create/', views.GroupCreateView.as_view(), name='group-create'),
    path('loadmore/remaining_users/', views.LoadMoreRemainingUsers.as_view(), name='load-more-remaining-users'),


    # Features
    path(r'api/chat/', include(router.urls)),
    path('api/msg/read/<int:pk>/', views.ReadUnReadMessage.as_view(), name='read-private-unread-msg'),
    path('api/group/msg/read/<int:pk>/', views.ReadGroupUnReadMessage.as_view(), name='read-group-unread-msg'),
    path('api/unread/msg/<int:pk>/', api.UnSeenMessageViewAPI.as_view(), name='api-unseen-private-msg'),
    path('api/unread/group/msg/<int:pk>/', api.GroupUnSeenMessageViewAPI.as_view(), name='api-unseen-group-msg'),

    # Delete Chat Message
    path('api/sender/msg/delete/<int:pk>/', views.DeleteSenderChatMessage.as_view(), name='api-delete-msg-sender'),
    path('api/sender/msg/delete/self/<int:pk>/', views.DeleteSenderChatMessageSelf.as_view(), name='api-delete-msg'
                                                                                                   '-sender-self'),
    path('api/receiver/msg/delete/<int:pk>/', views.DeleteReceiveChatMessage.as_view(), name='api-delete-msg-receiver'),

    path('api/chat/delete/combine/msg/<int:pk>/', views.DeleteCombineMessage.as_view(), name='api-delete-combine-msg'),
    path('api/chat/clear/all/chat/<int:pk>/', views.ClearAllChat.as_view(), name='api-clear-all-chat'),

    path('api/group/sender/msg/delete/<int:pk>/', views.DeleteSenderGroupChatMessage.as_view(), name='api-group'
                                                                                                     '-delete-msg'
                                                                                                     '-sender'),
    path('api/group/sender/msg/delete/self/<int:pk>/', views.DeleteSenderGroupChatMessageSelf.as_view(), name='api'
                                                                                                              '-group'
                                                                                                              '-delete-msg-sender-self'),
    path('api/group/receiver/msg/delete/<int:pk>/', views.DeleteReceiveGroupChatMessage.as_view(), name='api-group'
                                                                                                        '-delete-msg'
                                                                                                        '-receiver'),
    path('api/group/clear/all/chat/<int:pk>/', views.ClearAllGroupChat.as_view(), name='api-clear-all-group-chat'),
    path('api/group/combine/delete/<int:pk>/', views.DeleteCombineGroupMessage.as_view(),
        name='api-combine-group-chat'),

    path('group/member/list/<int:pk>/', views.GroupMemberListView.as_view(), name='group-member-list'),

    path('remove/from/group/<int:group_id>/<int:user_id>/', views.RemoveFromGroupView.as_view(), name='remove-from'
                                                                                                      '-group'),
    path('leave/from/group/<int:group_id>/<int:user_id>/', views.LeaveFromGroup.as_view(), name='leave-group'),

]