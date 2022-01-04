from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import authenticate

from app.models import User, Memo, Tag, Bookmark, Image


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


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Image
        fields = ['image']


# class LinkSerializer(serializers.ModelSerializer):
#     url = serializers.URLField
#
#     class Meta:
#         model = Link
#         fields = ['url']


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'


class MemoSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField(allow_null=True)
    #urls = LinkSerializer(many=True, write_only=True)
    tag_name = serializers.SerializerMethodField()
    tag_color = serializers.SerializerMethodField()
    #links = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='link_detail', allow_null=True)

    def get_images(self, obj):
        image = obj.image_set.all()
        return ImageSerializer(instance=image, many=True, context=self.context).data

    class Meta:
        model = Memo
        fields = ['id', 'memo_text', 'is_tag_new', 'url', 'tag_name', 'images',
                  'tag_color', 'tag', 'created_at', 'updated_at']

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
    tag_memos = MemoSerializer(many=True, write_only=True, allow_null=True)

    class Meta:
        model = Tag
        fields = ['tag_name', 'tag_color', 'user', 'tag_memos']
