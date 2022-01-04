import json
import requests
import string
import random

from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.serializers import TokenSerializer, MemoSerializer, UserSerializer, ImageSerializer
from app.models import User, Memo
from app.storages import get_s3_connection

from server.settings.base import env

def get_random_hash(length):
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(length):
        result += random.choice(string_pool)
    return result


# /hello
class HelloView(APIView):
    def get(self, request):
        return Response("GET Hello", status=200)

    def post(self, request):
        return Response("POST Hello", status=200)

    def patch(self, request):
        return Response("PATCH Hello", status=200)

    def delete(self, request):
        return Response("DELETE Hello", status=200)


# /users
class UserView(APIView):
    def get(self, request):
        if request.user.is_anonymous:
            return Response("알 수 없는 유저입니다.", status=404)

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=200)


# /auth/kakao
class KakaoLoginView(APIView):
    # 카카오 회원가입+로그인
    def post(self, request):
        data = JSONParser().parse(request)
        kakao_access_token = data.get('kakao_access_token', None)
        kakao_auth_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {kakao_access_token}",
            "Content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        kakao_response = requests.post(kakao_auth_url, headers=headers)
        kakao_response = json.loads(kakao_response.text)

        kakao_id = str(kakao_response.get('id', None))
        kakao_account = kakao_response.get('kakao_account', None)
        kakao_email = kakao_account.get('email', None)
        nickname = kakao_account.get('profile', None).get('nickname', None)

        user_data = {
            "kakao_id": kakao_id,
            "kakao_email": kakao_email,
            "nickname": nickname,
        }

        serializer = TokenSerializer(data=user_data)
        if serializer.is_valid():
            return Response(serializer.data, status=200)
        else:
            print(serializer.errors)
        return Response("Kakao Login False", status=400)


# /images
class ImagesView(APIView):
    def post(self, request):
        if request.user.is_anonymous:
            return Response("알 수 없는 유저입니다.", status=404)
        user_kakao_id = request.user.kakao_id
        image = request.FILES['image']
        memo_id = request.data['memo_id']

        hash_value = get_random_hash(length=30)
        directory = user_kakao_id + "/" + hash_value
        resource_url = "http://" + env('AWS_CLOUDFRONT_DOMAIN') + directory
        file_name = hash_value
        image_data = {
            "memo": memo_id,
            "url": resource_url,
            "name": file_name
        }
        serializer = ImageSerializer(data=image_data)
        if serializer.is_valid():
            s3 = get_s3_connection()
            s3.upload_fileobj(
                image,
                env('S3_BUCKET_NAME'),
                directory,
                ExtraArgs={
                    "ContentType": image.content_type,
                }
            )
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


# /memos
class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all().order_by('-created_at')
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination
