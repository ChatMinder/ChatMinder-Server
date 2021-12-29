from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class KakaoTokenSerializer():
    pass


class TokenSerializer(TokenObtainPairSerializer):
    # 유저가 존재하는지 인증 후, 해당 유저 토큰을 리턴
    pass
