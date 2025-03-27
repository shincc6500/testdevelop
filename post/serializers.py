from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()


# 댓글 Serializer
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # 작성자 이름 출력

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at']

# 게시글 Serializer
class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # ✅ 작성자 이름 (username)으로 보여줌
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'comments']

