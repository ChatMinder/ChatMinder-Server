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
    class Meta:
        model = Image
        fields = '__all__'


class MemoSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField(allow_null=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()

    def get_images(self, obj):
        image = obj.image_set.all()
        return ImageSerializer(instance=image, many=True, context=self.context).data

    class Meta:
        model = Memo
        fields = ['id', 'memo_text', 'url', 'tag', 'tag_name', 'tag_color', 'images', 'is_marked', 'timestamp',
                  'created_at', 'updated_at']

    def get_tag_name(self, obj):
        if obj.tag:
            return obj.tag.tag_name

    def get_tag_color(self, obj):
        if obj.tag:
            return obj.tag.tag_color

    # def create(self, validated_data):
    #     instance = Memo.objects.create(**validated_data)
    #     images_data = self.context['request'].FILES
    #     if images_data is not None:
    #         for images_data in images_data.getlist('image'):
    #             Image.objects.create(memo=instance, image=images_data)
    #     return instance


class TagSerializer(serializers.ModelSerializer):
    # memos = serializers.SerializerMethodField('get_memos_serializer')
    #
    # def get_memos_serializer(self, obj):
    #     memos = Memo.objects.filter(tag=obj, user=self.context.get('user'))
    #     serializer = MemoSerializer(memos, many=True, context=self.context)
    #     return serializer.data

    class Meta:
        model = Tag
        fields = ['id', 'tag_name', 'tag_color', 'user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'kakao_id', 'kakao_email', 'nickname',
                  'is_active', 'is_superuser', 'created_at', 'updated_at',
                  'last_login', 'created_at']

