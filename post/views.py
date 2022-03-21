from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from post.forms import PostCreateForm, PostCommentForm
from post.models import Category, Post, PostComment
from post.utils import image_process
from users.models import User


class PostIndex(LoginRequiredMixin, View):
    """
        :param request:
                authenticated_user, form-data,
        :return:
            Posts/False
    """

    def get(self, *args, **kwargs):
        context = {}
        context['post'] = []
        context['category'] = Category.objects.all()
        return render(self.request, 'post/feeds.html', context)

    def post(self, *args, **kwargs):
        print(self.request.POST)
        if not self.request.user.is_authenticated:
            return JsonResponse({
                "Status": False,
                'Message': "Authenticated user can post only!..."
            })
        # description = self.request.POST.get('description')
        # if not description:
        #     return JsonResponse({
        #         "Status": False,
        #         'Message': "Please specify topic description!..."
        #     })
        form = PostCreateForm(self.request.user, self.request.POST, self.request.FILES)
        if not form.is_valid():
            print(form.errors.as_json())
            return JsonResponse({
                "Status": False,
                'Message': "Required fields are empty!..."
            })
        post = form.save(commit=False)
        post.user = self.request.user
        for count, item in enumerate(self.request.FILES.getlist('images')):
            img = image_process(item)
            if img is None:
                return JsonResponse({
                    'status': False,
                    'message': "Only Image Files Are Acceptable!..."
                })
            if count == 0:
                post.image1 = img
            elif count == 1:
                post.image2 = img
            elif count == 2:
                post.image3 = img
            elif count == 3:
                post.image4 = img
            elif count == 4:
                post.image5 = img
            else:
                return JsonResponse({'status': False,
                                     'message': "Only 5 Image Files Are Acceptable!..."
                                     })
        post.save()

        post.description = self.request.POST.get('description')
        code = self.request.POST.get('code')

        post.save()

        return JsonResponse({
            'Status': True
        })


class LoadMorePost(View):
    def get(self, *args, **kwargs):
        self_post = self.request.GET.get('self')
        user_id = self.request.GET.get('user_id')
        if user_id:
            user = User.objects.filter(id=int(user_id)).last()
            if user:
                p = Paginator(Post.objects.filter(user=user), 10)
            else:
                p = Paginator(Post.objects.all(), 10)
        else:
            p = Paginator(Post.objects.all(), 2)

        if not self.request.GET.get('current_posts'):
            current_status = 0
        else:
            current_status = int(self.request.GET['current_posts'])

        if p.count <= current_status:
            return JsonResponse({
                'Status': False,
                'Message': 'No more posts!...'
            })
        new_posts = list(p.get_page((current_status + 2) / 2))
        posts = []
        for post in new_posts:

            if not post.user.profile_image:
                profile = "https://e7.pngegg.com/pngimages/798/436/png-clipart-computer-icons-user-profile-avatar-profile-heroes-black.png"
            else:
                profile = post.user.profile_image.url
            try:
                image1 = post.image1.url
            except ValueError:
                image1 = ""
            try:
                image2 = post.image2.url
            except ValueError:
                image2 = ""
            try:
                image3 = post.image3.url
            except ValueError:
                image3 = ""
            try:
                image4 = post.image4.url
            except ValueError:
                image4 = ""
            try:
                image5 = post.image5.url
            except ValueError:
                image5 = ""
            posts.append({
                'user': post.user.get_full_name(), 'user_id': post.user.id, 'profile': profile, 'post_id': post.id,
                'category': post.category.name,
                'description': post.description, 'likes': post.liked_by.count(),
                'username': post.user.username, 'timestamp': post.timestamp.strftime("%d %b %y - %H:%M %p "),
                'like_status': True if self.request.user in post.liked_by.all() else False, 'image1': image1,
                'comments': PostComment.objects.filter(post=post).count(), 'image2': image2, 'image3': image3,
                'image4': image4, 'image5': image5, 'type': 'post'
            })
        return JsonResponse({'posts': posts})

class LoadMoreComments(View):
    def get(self, *args, **kwargs):
        post_id = self.request.GET.get('post_id')
        post = Post.objects.filter(id=post_id).last()

        if not post:
            return JsonResponse({})
        comment_list = PostComment.objects.filter(post=post)
        p = Paginator(comment_list, 4)

        current_status = int(self.request.GET.get('current_comments'))
        if p.count <= current_status:
            return JsonResponse({
                'Status': False,
                'Message': 'No more posts!...'
            })
        new_comments = list(p.get_page((current_status + 2) // 2))
        comments = []
        for item in new_comments:
            if not item.user.get_profile_img():
                profile = "https://e7.pngegg.com/pngimages/798/436/png-clipart-computer-icons-user-profile-avatar-profile-heroes-black.png"
            else:
                profile = item.user.get_profile_img()
            comments.append({
                'id': item.id,
                'post_id': item.post.id,
                'comment': item.comment,
                'timestamp': item.timestamp.strftime("%d %b, %Y"),
                'post_user_id': item.user.id,
                'user': item.user.username,
                'post_user': item.user.get_full_name(),
                'user_email': item.user.email,
                'user_profile': profile,
            })

        return JsonResponse({
            'comments': comments
        })

class PostComments(View):
    """
    :param request:
        authenticated_user, post-id, form-data,
    :return:
        Comments/False
    """

    def get(self, *args, **kwargs):
        post = Post.objects.filter(id=id).last()
        if not post:
            return JsonResponse({
                'status': False,
                'Message': 'Invalid post id!...'
            })
        else:
            return JsonResponse({
                'status': True,
                'post_id': post.id,
            })


    def post(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return JsonResponse({
                "status": False,
                'Message': "Authenticated user can comment only!..."
            })
        id = self.request.POST.get('id')
        type = self.request.POST.get('type')
        post = Post.objects.filter(id=int(id)).last()
        print(post)
        if not post:
            return JsonResponse({
                'status': False,
                'Message': 'Invalid post id!...'
            })
        form = PostCommentForm(self.request.user, self.request.POST)
        if not form.is_valid():
            return JsonResponse({
                'status': False,
                'Message': 'Invalid data!...'
            })
        comment = form.save(commit=False)
        comment.user = self.request.user
        comment.post = post
        comment.save()
        return JsonResponse({'status': True, 'id': post.id, 'type': 'post'})

class GetComment(View):
    def get(self, *args, **kwargs):
        post_id = self.request.GET.get('post_id')
        post = Post.objects.filter(id=post_id).last()
        comment_list = PostComment.objects.filter(post=post).first()
        comment_list = [comment_list]
        comments = []

        for item in comment_list:

            if not item.user.get_profile_img():
                profile = "https://e7.pngegg.com/pngimages/798/436/png-clipart-computer-icons-user-profile-avatar-profile-heroes-black.png"
            else:
                profile = item.user.get_profile_img()
            comments.append({
                'id': item.id,
                'post_id': item.post.id,
                'comment': item.comment,
                'timestamp': item.timestamp.strftime("%d %b, %Y"),
                'post_user_id': item.user.id,
                'user': item.user.username,
                'post_user': item.user.get_full_name(),
                'user_email': item.user.email,
                'user_profile': profile
            })

        return JsonResponse({
            'comments': comments
        })


@method_decorator(csrf_exempt, name='dispatch')
class PostLike(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        """
        :param request:
            authenticated_user, post-id,
        :return:
            True/False, Number of likes
        """
        id = self.request.POST.get('id')
        if not id:
            return JsonResponse({
                'Status': False,
                'Message': 'ID is required!...'
            })
        post = Post.objects.filter(id=id).get()
        if self.request.user not in post.liked_by.all():
            post.liked_by.add(self.request.user)
        else:
            post.liked_by.remove(self.request.user)
        return JsonResponse({
            'likes': post.liked_by.all().count()
        })

class SampleView(View):
    def get(self, *args, **kwargs):
        return render(self.request, 'post/sample.html')