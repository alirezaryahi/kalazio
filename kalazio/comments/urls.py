from django.urls import path
from .views import CreateComment, LikeCommentCreate, DisLikeCommentCreate, MyComments, WaitingComment, ImageComments

urlpatterns = [
    path('create/', CreateComment.as_view()),
    path('like-comment/', LikeCommentCreate.as_view()),
    path('dislike-comment/', DisLikeCommentCreate.as_view()),
    path('my-comment/', MyComments.as_view()),
    path('image-comments/', ImageComments.as_view()),
    path('waiting-comment/', WaitingComment.as_view()),
]
