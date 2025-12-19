# posts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("pk", "username")

class CommentSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("pk", "user", "content", "created_at")
        read_only_fields = ("pk", "user", "created_at")

class PostListSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    comments_count = serializers.IntegerField(source="comment_set.count", read_only=True)

    class Meta:
        model = Post
        fields = ("pk", "user", "title", "content", "created_at", "updated_at", "comments_count")

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("pk", "title", "content")
        read_only_fields = ("pk",)

class PostDetailSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    comments = CommentSerializer(source="comment_set", many=True, read_only=True)

    class Meta:
        model = Post
        fields = ("pk", "user", "title", "content", "created_at", "updated_at", "comments")
