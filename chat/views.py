import json
import uuid
from datetime import timedelta, datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import CreateView
from rest_framework import generics, permissions

from chat.forms import GroupCreateForm
from chat.models import GroupChatModel, P2pChatModel, GroupChat
from chat.serializers import P2pChatModelSerializer, GroupChatModelSerializer
from users.models import User


def arrange_users(users):
    chat_list = {}
    for user in users:
        username = user.username
        #         # print(username)
        if username[0].upper() not in chat_list.keys():
            chat_list[username[0].upper()] = []
            chat_list[username[0].upper()].append(username)
        else:
            if username not in chat_list[username[0].upper()]:
                chat_list[username[0].upper()].append(username)
    chat_list_order = sorted(chat_list.keys(), key=lambda x: x.lower())
    accounts = []
    for item in chat_list_order:
        initial = [item]
        chats = [chat_list[item]]
        # print(chats)
        accounts.append([initial, chats])
    account_dict = {}
    for item in accounts:
        account_dict[item[0][0]] = []
        for username in item[1][0]:
            user = User.objects.filter(username=username).last()
            account_dict[item[0][0]].append(user)
    return account_dict


class HomeView(View):
    def get(self, *args, **kwargs):
        context = {}
        user = self.request.user

        users = user.get_user_connected_users()
        context['chat_list_user'] = users
        context['contact_list'] = users
        context['group_list'] = self.request.user.groups.all()
        account_dict = arrange_users(users)
        # remaining_users = user.get_remaining_users()
        # remaining_dict = arrange_users(remaining_users)
        # context['remaining_dict'] = remaining_dict
        context['accounts'] = account_dict
        context['room_name_json'] = mark_safe(json.dumps('room_name'))
        context['session_key'] = mark_safe(json.dumps(self.request.session.session_key))
        context['user'] = user

        return render(self.request, 'chat/chat-direct.html', context)


class GroupCreateView(CreateView):
    model = GroupChatModel
    form_class = GroupCreateForm

    def form_valid(self, form):
        print(self.request.POST)
        user = self.request.user
        group = form.instance
        group.created_by = user
        group.member_count = 1
        group.save()
        today = datetime.now().date()
        group.save()
        group.admin.add(user)
        group_name = str(uuid.uuid1())
        # group.name = re.sub(r"\s+", "", group.group_name, flags=re.UNICODE)
        group.name = group_name
        group.save()
        group_create_user = self.request.user
        group_create_user.groups.add(group)
        group_create_user.save()
        users = self.request.POST.getlist('groupMember[]')
        if users:
            for id in users:
                user = User.objects.filter(id=int(id)).last()
                user.groups.add(group)
                user.save()
                group.member_count = group.member_count + 1
                group.save()
        return redirect('chat:chat')


class GroupUpdateView(View):
    def get(self, *args, **kwargs):
        return HttpResponse("Group Update")


class LoadMoreRemainingUsers(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        user = self.request.user
        remaining_users = user.get_remaining_users().order_by('username')
        p = Paginator(remaining_users, 10)
        current_status = int(self.request.GET['current_users'])
        remaining_dict = arrange_users(p.get_page((current_status + 10) / 10))
        if p.count <= current_status:
            return JsonResponse({
                'status': False,
                'message': 'No more users found!...'
            })
        result = {}
        for key, values in remaining_dict.items():
            user_list = []
            for user in values:
                user_list.append({
                    'id': user.id,
                    'name': user.get_full_name(),
                    'username': user.username,
                    'profile': reverse('friend-profile', kwargs={'pk': user.id}),
                    'profile_img': user.get_profile_img(),
                })
            result[key] = user_list
        return JsonResponse({'users': result})


class ReadUnReadMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        sender_id = self.kwargs.get('pk')
        sender = User.objects.filter(id=sender_id).last()
        if sender:
            message = P2pChatModel.objects.filter(recipient=self.request.user, user=sender, read=False)
            if message:
                for item in message:
                    item.read = True
                    item.save()
                return JsonResponse({
                    'status': True,
                    'read': True
                })
            return JsonResponse({
                'status': False,
                'error': 'No new messages'
            })
        return JsonResponse({
            'status': False,
            'error': 'Sender does not exist!'
        })


class ReadGroupUnReadMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        group_id = self.kwargs.get('pk')
        group = GroupChatModel.objects.filter(id=group_id).last()
        if group:
            chats = GroupChat.objects.filter(group=group).exclude(user_read__in=[self.request.user])
            if chats:
                for item in chats:
                    item.user_read.add(self.request.user)
                    item.save()
                return JsonResponse({
                    'status': True,
                    'read': True
                })
            return JsonResponse({
                'status': False,
                'error': 'No new messages'
            })
        return JsonResponse({
            'status': False,
            'error': 'Sender does not exist!'
        })


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
            chats = GroupChat.objects.filter(group=group).exclude(user_read__in=[self.request.user])
            return chats
        return None


class DeleteSenderChatMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = P2pChatModel.objects.filter(id=chat_id, user=self.request.user).last()
        if chat:
            chat.body = "This message was deleted."
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Message deleted!'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class DeleteSenderChatMessageSelf(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = P2pChatModel.objects.filter(id=chat_id, user=self.request.user).last()
        if chat:
            chat.is_delete = True
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Message deleted from sender system!'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class DeleteReceiveChatMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = P2pChatModel.objects.filter(id=chat_id, recipient=self.request.user).last()
        if chat:
            chat.is_receiver_delete = True
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Message deleted from receiver system!'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class DeleteCombineMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = P2pChatModel.objects.filter(id=chat_id).last()
        if chat:
            if chat.user == self.request.user or chat.recipient == self.request.user:
                chat.is_receiver_delete = True
                chat.save()
                return JsonResponse({
                    'status': True,
                    'error': 'Message deleted from receiver system in a loop!'
                })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class ClearAllChat(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        receiver_id = self.kwargs.get('pk')
        receiver = User.objects.filter(id=receiver_id).last()
        if receiver:
            chats = P2pChatModel.objects.filter(user=self.request.user, recipient=receiver)
            for chat in chats:
                chat.is_delete = True
                chat.save()

            chats = P2pChatModel.objects.filter(user=receiver, recipient=self.request.user)
            for chat in chats:
                chat.is_receiver_delete = True
                chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Clear Message system!'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class DeleteSenderGroupChatMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = GroupChat.objects.filter(id=chat_id).last()
        if chat.group in self.request.user.groups.all() and chat.user == self.request.user:
            chat.body = "This message was deleted."
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Message deleted from sender system!'
            })
        return JsonResponse({
            'status': True,
            'error': 'Message not found!'
        })


class DeleteSenderGroupChatMessageSelf(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = GroupChat.objects.filter(id=chat_id).last()
        if chat.group in self.request.user.groups.all() and chat.user == self.request.user:
            chat.is_delete = True
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Message deleted from sender system!'
            })
        return JsonResponse({
            'status': True,
            'error': 'Message not found!'
        })


class ClearAllGroupChat(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        group_id = self.kwargs.get('pk')
        group = GroupChatModel.objects.filter(id=group_id).last()
        if group and group in self.request.user.groups.all():
            group_chat = GroupChat.objects.filter(group=group)
            for chat in group_chat:
                if chat.user == self.request.user:
                    chat.is_delete = True
                    chat.save()
                else:
                    chat.receiver_delete.add(self.request.user)
                    chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Clear Message system!'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class DeleteCombineGroupMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = GroupChat.objects.filter(id=chat_id).last()
        # print(chat)
        if chat and chat.group in self.request.user.groups.all():
            if chat.user == self.request.user:
                chat.is_delete = True
            else:
                chat.receiver_delete.add(self.request.user)
            chat.save()
            return JsonResponse({
                'status': True,
                'error': 'Clear Message system!'
            })
        return JsonResponse({
            'status': True,
            'error': 'Message not Found!'
        })


class DeleteReceiveGroupChatMessage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        chat_id = self.kwargs.get('pk')
        chat = GroupChat.objects.filter(id=chat_id).last()
        if chat.group in self.request.user.groups.all():
            chat.receiver_delete.add(self.request.user)
            chat.save()
            return JsonResponse({
                'status': False,
                'error': 'Message cleared from system'
            })
        return JsonResponse({
            'status': False,
            'error': 'Message not found'
        })


class GroupMemberListView(View):
    def get(self, *args, **kwargs):
        group = GroupChatModel.objects.filter(id=self.kwargs.get('pk')).last()
        if group and group in self.request.user.groups.all():
            if group:
                users = User.objects.filter(groups__in=[group])
                user_list = {}

                for user in users:
                    if user in group.admin.all():
                        user_list[user.id] = f"{user.first_name} {user.last_name},{user.email},true,{user.username}"
                    else:
                        user_list[user.id] = f"{user.first_name} {user.last_name},{user.email},false,{user.username}"

                return JsonResponse({
                    'member_list': user_list,
                    'created_by': f"{group.created_by.first_name} {group.created_by.last_name},{group.created_by.email},true",
                    'info': group.group_info,
                    'created_at': f"{group.created_at.date()},{group.created_at.time()}",
                })
            return JsonResponse({
                "error": "Group not found."
            })
        return JsonResponse({
            "error": "Group not exist."
        })


class AddMemberToGroupView(View):
    def get(self, *args, **kwargs):
        group = GroupChatModel.objects.filter(id=self.request.GET.get('pk')).last()
        if not group:
            return JsonResponse({
                'error': "Group not exist!",
            })
        if self.request.user not in group.admin.all():
            return JsonResponse({
                'error': 'Only admin can add member to group',
            })
        user_ids = self.request.GET.getlist('user_ids[]')
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            # Creator is not counted in total group members size
            user.groups.add(group)
            group.member_count = group.member_count + 1
            group.save()
            user.save()
        return JsonResponse({
            'data': 'Member(s) added to Group.'
        })


class RemoveFromGroupView(View):
    def get(self, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        user_id = self.kwargs.get('user_id')
        group = GroupChatModel.objects.filter(id=group_id).last()
        user = User.objects.filter(id=user_id).last()

        if not group:
            return JsonResponse({
                'error': "Group not exist",
            })
        if not self.request.user == group.created_by:
            return JsonResponse({
                'error': 'Only Group creator can remove member from group',
            })
        if group not in user.groups.all():
            return JsonResponse({
                'error': 'User doesn\'t belongs to group.',
            })

        user.groups.remove(group)
        group.member_count = group.member_count - 1
        group.save()
        user.save()
        return JsonResponse({
            'data': 'User removed from group',
        })


class LeaveFromGroup(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        user_id = self.kwargs.get('user_id')
        group = GroupChatModel.objects.filter(id=group_id).last()
        user = User.objects.filter(id=user_id).last()

        if not group:
            return JsonResponse({
                'error': "Group not exist",
            })
        if group not in user.groups.all():
            return JsonResponse({
                'error': 'User doesn\'t belongs to group.',
            })
        user.groups.remove(group)
        user.save()
        group.member_count = group.member_count - 1
        group.save()
        group_chat = GroupChat(group=group, user=user, body=f"{user.email} left.")
        group_chat.save()
        return JsonResponse({
            'data': 'User left group',
        })
