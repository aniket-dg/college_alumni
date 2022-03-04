from django import forms

from chat.models import GroupChatModel
# from post.models import Post


# class PostCreateForm(forms.ModelForm):
#     class Meta:
#         model = Post
#         exclude = ['likes', 'timestamp','image2', 'image3', 'image4',
#                   'image5', "skeleton_code", "liked_by"]


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = GroupChatModel
        fields = ['group_name', 'profile_image', 'group_info']