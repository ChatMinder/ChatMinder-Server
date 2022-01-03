from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import authenticate

from app.models import User, Memo, Tag, Bookmark


class TokenSerializer(TokenObtainPairSerializer):
    kakao_email = serializers.EmailField(write_only=True, required=False)
    nickname = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    kakao_id = serializers.CharField()

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['kakao_id'] = user.kakao_id
        token['kakao_email'] = user.kakao_email
        return token

    def validate(self, data):
        user, created = User.objects.get_or_create(
            kakao_id=data.get('kakao_id', None),
            kakao_email=data.get('kakao_email', None)
        )
        if created:
            user.set_password(None)
        user.nickname = data.get('nickname', None)
        user.is_active = True
        user.save()

        authenticate(username=user.USERNAME_FIELD)

        validated_data = super().validate(data)
        refresh = self.get_token(user)
        validated_data["refresh"] = str(refresh)
        validated_data["access"] = str(refresh.access_token)
        validated_data["kakao_id"] = user.kakao_id
        return validated_data


# class ImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Image
#         fields = '__all__'
#
#
# class LinkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Link
#         fields = '__all__'


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'


class MemoSerializer(serializers.ModelSerializer):
    memo_mark = BookmarkSerializer(write_only=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()

    class Meta:
        model = Memo
        fields = ['id', 'memo_text',  'url', 'image','is_tag_new','memo_mark',
                  'tag_name', 'tag_color', 'tag', 'created_at', 'updated_at']

    def get_tag_name(self, obj):
        return obj.tag.tag_name

    def get_tag_color(self, obj):
        return obj.tag.tag_color


class TagSerializer(serializers.ModelSerializer):
    tag_memos = MemoSerializer(many=True, write_only=True, allow_null=True)

    class Meta:
        model = Tag
        fields = ['tag_name', 'tag_color', 'user', 'tag_memos']
