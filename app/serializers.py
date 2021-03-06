from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import authenticate

from app.models import User, Memo, Tag, Image

def user_created_init(attrs, user):
    color = '#C8D769'
    timestamp = attrs.get('timestamp', None)
    tag = Tag.objects.create(tag_name='태그입력',
                             tag_color=color,
                             user=user)
    tag.save()
    memo = Memo.objects.create(memo_text='첫번째 메모를 작성해 보세요.',
                               timestamp=timestamp,
                               tag=tag, user=user, is_marked=True)
    memo.save()


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class TokenSerializer(TokenObtainPairSerializer):
    kakao_email = serializers.EmailField(write_only=True, required=False, allow_null=True)
    nickname = serializers.CharField(write_only=True, required=False)
    kakao_id = serializers.CharField()
    timestamp = serializers.CharField(write_only=True)

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
        attrs.update({'password': None})
        user, created = User.objects.get_or_create(
            kakao_id=attrs.get('kakao_id', None),
            kakao_email=attrs.get('kakao_email', None)
        )
        user.nickname = attrs.get('nickname', None)
        user.is_active = True
        user.save()

        if created:
            user_created_init(attrs, user)

        authenticate(username=user.USERNAME_FIELD, is_kakao=True)

        validated_data = super().validate(attrs)
        refresh = self.get_token(user)
        validated_data["refresh"] = str(refresh)
        validated_data["access"] = str(refresh.access_token)
        validated_data["kakao_id"] = user.kakao_id
        return validated_data


class ImageSerializer(serializers.ModelSerializer):
    # memo_id = serializers.ReadOnlyField(source='memo.id')
    # user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = Image
        # fields = '__all__'
        fields = ['memo', 'user', 'url']
        extra_kwargs = {
            'memo': {
                'write_only': True
            },
            'user': {
                'write_only': True
            },
            # 'file': {
            #     'write_only': True,
            #     'required': False
            # }
        }


class MemoSerializer(DynamicFieldsModelSerializer):
    images = serializers.SerializerMethodField(allow_null=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()
    tag_id = serializers.SerializerMethodField()

    def get_images(self, obj):
        image = obj.image_set.all()
        return ImageSerializer(instance=image, many=True, context=self.context).data

    class Meta:
        model = Memo
        fields = ['id', 'memo_text', 'url', 'tag_id', 'tag_name', 'tag_color', 'images', 'is_marked', 'timestamp']

    def get_tag_name(self, obj):
        if obj.tag:
            return obj.tag.tag_name

    def get_tag_color(self, obj):
        if obj.tag:
            return obj.tag.tag_color

    def get_tag_id(self, obj):
        if obj.tag:
            return obj.tag.id
        else:
            return None


class MemoLinkSerializer(serializers.ModelSerializer):
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()
    tag_id = serializers.SerializerMethodField()

    class Meta:
        model = Memo
        fields = ['id', 'memo_text', 'url', 'tag_id', 'tag_name', 'tag_color', 'is_marked', 'timestamp']

    def get_tag_name(self, obj):
        if obj.tag:
            return obj.tag.tag_name

    def get_tag_color(self, obj):
        if obj.tag:
            return obj.tag.tag_color

    def get_tag_id(self, obj):
        if obj.tag:
            return obj.tag.id
        else:
            return None


class TagSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'tag_name', 'tag_color', 'user_id']

    def get_user_id(self, obj):
        return obj.user.id


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'kakao_id', 'kakao_email', 'nickname',
#                   'is_active', 'is_superuser', 'last_login']

class UserSerializer(serializers.ModelSerializer):
    kakao_id = serializers.CharField()
    password = serializers.CharField(write_only=True)
    timestamp = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        kakao_id = validated_data.get('kakao_id')
        password = validated_data.get('password')
        user = User(
            kakao_id=kakao_id,
        )
        user.set_password(password)
        user.save()
        user_created_init(validated_data, user)
        return user

class UserTokenSerializer(TokenObtainPairSerializer):
    kakao_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['kakao_id'] = user.kakao_id
        token['kakao_email'] = user.kakao_email
        return token

    def validate(self, attrs):
        user = User.objects.get(
            kakao_id=attrs.get('kakao_id', None),
        )
        password = attrs.get('password')
        authenticate(username=user.USERNAME_FIELD, password=password)
        validated_data = super().validate(attrs)
        refresh = self.get_token(user)
        validated_data["refresh"] = str(refresh)
        validated_data["access"] = str(refresh.access_token)
        validated_data["kakao_id"] = user.kakao_id
        return validated_data
