from rest_framework import serializers
from post.models import Post, PostComment


class PostCommentSerilizer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    user_profile = serializers.CharField(source='user.profile_image')
    post_id = serializers.IntegerField(source='post.id')
    post_user = serializers.CharField(source='post.user.get_full_name')
    post_user_id = serializers.CharField(source='post.user.id')
    timestamp = serializers.SerializerMethodField('get_timestamp')

    class Meta:
        model = PostComment
        fields = ['user', 'user_profile', 'comment', 'timestamp', 'post_user', 'post_id', 'post_user_id']

    def get_image_url(self, obj):
        if obj.user_profile:
            return obj.user.user_profile.url
        return ''

    def get_timestamp(self, obj):
        timestamp = obj.timestamp
        if timestamp:
            return timestamp.strftime("%d %b, %Y")
        return ''

