import json
import requests

from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from app.serializers import TokenSerializer


class HelloView(APIView):
    def get(self, request):
        return Response("GET Hello", status=200)

    def post(self, request):
        return Response("POST Hello", status=200)

    def patch(self, request):
        return Response("PATCH Hello", status=200)

    def delete(self, request):
        return Response("DELETE Hello", status=200)


# /auth/kakao
class KakaoLoginView(APIView):
    @staticmethod
    def post(request):
        data = JSONParser().parse(request)
        kakao_access_token = data.get('kakao_access_token', None)
        kakao_auth_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {kakao_access_token}",
            "Content-type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        kakao_response = requests.post(kakao_auth_url, headers=headers)
        kakao_response = json.loads(kakao_response.text)

        # debug
        print(kakao_response)

        # 유저 존재 -> 유저 토큰 가져옴
        # 유저 존재 x -> 유저 DB에 생성 후 토큰 가져옴

        serializer = TokenSerializer(data=kakao_response)
        if serializer.is_valid():
            return Response(serializer.data, status=200)
        return Response("Kakao Login False", status=400)
