from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework import views, generics, permissions

from chat.models import P2pChatModel, GroupChat, GroupChatModel, GroupChatUnreadMessage
from chat.serializers import P2pChatModelSerializer, UserModelSerializer, GroupChatModelSerializer
from users.models import User

from django_filters.rest_framework import DjangoFilterBackend

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class MessagePagination(PageNumberPagination):
    page_size = 10


class P2pChatModelViewSet(ModelViewSet):
    queryset = P2pChatModel.objects.all()
    serializer_class = P2pChatModelSerializer
    allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS')
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = MessagePagination
    filter_backends = [DjangoFilterBackend]
    search_fields = ['body']

    def list(self, request, *args, **kwargs):
        body = self.request.GET.get('body')
        self.queryset = self.queryset.filter(Q(recipient=request.user) |
                                             Q(user=request.user))
        if body:
            self.queryset = self.queryset.filter(Q(recipient=request.user) |
                                             Q(user=request.user), body__contains=body)
        target = self.request.query_params.get('target', None)
        if target is not None:
            self.queryset = self.queryset.filter(
                Q(recipient=request.user, user__email=target) |
                Q(recipient__email=target, user=request.user))
        return super(P2pChatModelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        msg = get_object_or_404(
            self.queryset.filter(Q(recipient=request.user) |
                                 Q(user=request.user),
                                 Q(pk=kwargs['pk'])))
        serializer = self.get_serializer(msg)
        return Response(serializer.data)


class GroupChatModelViewSet(ModelViewSet):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatModelSerializer
    allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS')
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = MessagePagination

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.all()
        target = self.request.query_params.get('target', None)
        if target is not None:
            self.queryset = self.queryset.filter(
                Q(group__name=target))
        return super(GroupChatModelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        msg = get_object_or_404(
            self.queryset.filter(Q(pk=kwargs['pk'])))
        serializer = self.get_serializer(msg)
        return Response(serializer.data)


class UserModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    allowed_methods = ('GET', 'HEAD', 'OPTIONS')
    pagination_class = None  # Get all user

    def list(self, request, *args, **kwargs):
        # Get all users except yourself
        self.queryset = self.queryset.exclude(id=request.user.id)
        return super(UserModelViewSet, self).list(request, *args, **kwargs)


class UnSeenMessageViewAPI(generics.ListAPIView):
    serializer_class = P2pChatModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        receiver_id = self.kwargs.get('pk')
        receiver = User.objects.filter(id=receiver_id).last()
        if receiver:
            unread_chat = P2pChatModel.objects.filter(user=receiver, recipient=self.request.user).filter(read=False)
            return unread_chat



class GroupUnSeenMessageViewAPI(generics.ListAPIView):
    serializer_class = GroupChatModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_chat_id = self.kwargs.get('pk')
        group = GroupChatModel.objects.filter(id=group_chat_id).last()
        if group:
            chats = GroupChat.objects.filter(group=group).exclude(user_read__in = [self.request.user])
            return chats
        return None

