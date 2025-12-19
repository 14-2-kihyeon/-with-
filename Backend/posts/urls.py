# posts/urls.py
from django.urls import path
from . import views

app_name = "posts"

urlpatterns = [
    path("", views.PostListCreateView.as_view(), name="post_list_create"),
    path("<int:pk>/", views.PostRetrieveUpdateDestroyView.as_view(), name="post_detail"),
    path("<int:pk>/comments/", views.CommentCreateView.as_view(), name="comment_create"),
    path("<int:post_pk>/comments/<int:comment_pk>/", views.CommentDeleteView.as_view(), name="comment_delete"),
]
