from rest_framework import serializers
from django.shortcuts import get_object_or_404

from chat.models import P2pChatModel, GroupChat, UserMedia, UploadedMedia
from users.models import User

class UploadedMediaSerailizer(serializers.ModelSerializer):

    def to_representation(self, instance):
        response = super().to_representation(instance)
        return response.get('media', None)

    class Meta:
        model = UploadedMedia
        fields = ('media',)


class P2pChatModelSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.CharField(source='user.id', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    recipient_full_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    recipient = serializers.CharField(source='recipient.email')
    recipient_id = serializers.CharField(source='recipient.id')
    user_profile_url = serializers.CharField(source='user.profile_image.url')
    recipient_profile_url = serializers.CharField(source='recipient.profile_image.url')
    timestamp = serializers.DateTimeField(format="%I:%M")
    media_files = serializers.SerializerMethodField('get_media_files')

    def get_media_files(self, instance):
        if instance.is_media_present:
            uploaded_media_files = UploadedMediaSerailizer(instance.bucket.files, many=True).data
            return uploaded_media_files
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        recipient = get_object_or_404(
            User, email=validated_data['recipient']['email'])
        msg = P2pChatModel(recipient=recipient, body=validated_data['body'], user=user)
        msg.save()
        print("Message save", msg.id)
        return msg

    class Meta:
        model = P2pChatModel
        fields = ('id', 'user', 'user_full_name','user_id','recipient','recipient_full_name','recipient_id','is_media_present','bucket', 'media_files', 'timestamp', 'body','recipient_profile_url','user_profile_url','is_delete','is_receiver_delete')


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','email','username')

class GroupChatModelSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.CharField(source='user.id', read_only=True)
    receiver_delete = UserModelSerializer(read_only=True, many=True)
    group_name = serializers.CharField(source='group.group_name')
    group_id = serializers.CharField(source='group.id')
    user_profile_url = serializers.CharField(source='user.profile_image.url')
    group_profile_url = serializers.CharField(source='group.profile_image.url')
    timestamp = serializers.DateTimeField(format="%I:%M")
    media_files = serializers.SerializerMethodField('get_media_files')
    user_full_name = serializers.CharField(source='user.get_full_name')

    def get_media_files(self, instance):
        if instance.is_media_present:
            uploaded_media_files = UploadedMediaSerailizer(instance.bucket.files, many=True).data
            return uploaded_media_files
        return None

    class Meta:
        model = GroupChat
        fields = ('id', 'user', 'user_id','group_name', 'group_id','user_profile_url','is_media_present','bucket', 'media_files', 'body','receiver_delete','group_profile_url','timestamp','is_delete','user_full_name')


