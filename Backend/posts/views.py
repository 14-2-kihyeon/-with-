# posts/views.py
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404

from .models import Post, Comment
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsCommentOwner


# /posts/  (GET: 목록, POST: 생성)
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all().select_related("user").order_by("-pk")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostListSerializer
        return PostCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# /posts/<pk>/  (GET: 상세, PUT/PATCH: 수정, DELETE: 삭제)
class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all().select_related("user")
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostDetailSerializer
        return PostCreateUpdateSerializer


# /posts/<pk>/comments/  (POST: 댓글 생성)
class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        serializer.save(post=post, user=self.request.user)


# /posts/<post_pk>/comments/<comment_pk>/  (DELETE: 댓글 삭제)
class CommentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsCommentOwner]

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs["comment_pk"])

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance)
        instance.delete()
