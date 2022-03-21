from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api
from . import views
app_name = 'post'

router = DefaultRouter()
router.register(r'cmt', api.PostCommentModelViewSet, basename='api-comment')

postcomment_list = api.PostCommentModelViewSet.as_view({
    'get': 'list',
})


urlpatterns = [
    path('', views.PostIndex.as_view(), name='post'),
    path('loadmore/post/', views.LoadMorePost.as_view(), name='load-more-post'),
    path('loadMore/comments/', views.LoadMoreComments.as_view(), name='load-more-comments'),
    path('comment/', views.PostComments.as_view(), name='comment'),
    path('get/comment/', views.GetComment.as_view(), name='get-single-comment'),
    path('like/', views.PostLike.as_view(), name='like'),
    path('sample/', views.SampleView.as_view(), name='sample'),
]