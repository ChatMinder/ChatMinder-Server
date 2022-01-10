from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import authenticate

from app.models import User, Memo, Tag, Image


class TokenSerializer(TokenObtainPairSerializer):
    kakao_email = serializers.EmailField(write_only=True, required=False)
    nickname = serializers.CharField(write_only=True, required=False)
    kakao_id = serializers.CharField()

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['kakao_id'] = user.kakao_id
        token['kakao_email'] = user.kakao_email
        return token

    def validate(self, attrs):
        attrs.update({'password': ''})
        user, created = User.objects.get_or_create(
            kakao_id=attrs.get('kakao_id', None),
            kakao_email=attrs.get('kakao_email', None)
        )
        user.nickname = attrs.get('nickname', None)
        user.is_active = True
        user.save()

        authenticate(username=user.USERNAME_FIELD)

        validated_data = super().validate(attrs)
        refresh = self.get_token(user)
        validated_data["refresh"] = str(refresh)
        validated_data["access"] = str(refresh.access_token)
        validated_data["kakao_id"] = user.kakao_id
        return validated_data


class ImageSerializer(serializers.ModelSerializer):
    memo_id = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'url', 'name', 'user_id', 'memo_id']

    def get_user_id(self, obj):
        return obj.user.id

    def get_memo_id(self, obj):
        return obj.memo.id


class MemoSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField(allow_null=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()
    tag_id = serializers.SerializerMethodField()

    def get_images(self, obj):
        image = obj.image_set.all()
        return ImageSerializer(instance=image, many=True, context=self.context).data

    class Meta:
        model = Memo
        fields = ['id', 'memo_text', 'url', 'tag_id', 'tag_name', 'tag_color', 'images', 'is_marked', 'timestamp',
                  'created_at', 'updated_at']

    def get_tag_name(self, obj):
        if obj.tag:
            return obj.tag.tag_name

    def get_tag_color(self, obj):
        if obj.tag:
            return obj.tag.tag_color

    def get_tag_id(self, obj):
        if obj.tag:
            print(obj.tag)
            return obj.tag.id
        else:
            return None


class TagSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'tag_name', 'tag_color', 'user_id', 'created_at', 'updated_at']

    def get_user_id(self, obj):
        return obj.user.id



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'kakao_id', 'kakao_email', 'nickname',
                  'is_active', 'is_superuser', 'created_at', 'updated_at',
                  'last_login', 'created_at']

