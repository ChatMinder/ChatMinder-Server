from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import authenticate

from app.models import User


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
