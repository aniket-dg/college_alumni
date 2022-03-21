from django import forms

from .models import Post, PostComment


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['description', 'image1','category']
        exclude = ['liked_by', 'timestamp', 'user', 'image2', 'image3', 'image4',
                   'image5']

    def __init__(self, user, *args, **kwargs):
        super(PostCreateForm, self).__init__(*args, **kwargs)
        self.user = user


class PostCommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ['comment']
        exclude = ['post', 'timestamp', 'user']

    def __init__(self, user, *args, **kwargs):
        super(PostCommentForm, self).__init__(*args, **kwargs)
        self.user = user
