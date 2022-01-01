import json
import requests
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters

from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.serializers import TokenSerializer, MemoSerializer
from app.models import User, Memo


class MemoFilter(FilterSet):
    memo_text = filters.CharFilter(field_name='memo_text', lookup_expr="icontains")
    link = filters.CharFilter(field_name='link', lookup_expr="icontains")
    is_marked = filters.BooleanFilter(field_name='is_marked') #뷱마크 모아보기
    image_null = filters.BooleanFilter(field_name='image', method='is_image_null') #이미지 모아보기
    link_null = filters.BooleanFilter(field_name='link', method='is_link_null') #링크 모아보기
    is_text_null = filters.BooleanFilter(field_name='memo_text', method='is_text_null') #텍스트 모아보기

    class Meta:
        model = Memo
        fields = ['memo_text', 'image', 'is_marked', 'link']

    def is_image_null(self, queryset, image, value):
        if value:
            return queryset.filter(image__isnull=True)
        else:
            return queryset.filter(image__isnull=False)

    def is_link_null(self, queryset, link, value):
        if value:
            return queryset.filter(link__isnull=True)
        else:
            return queryset.filter(link__isnull=False)

    def is_text_null(self, queryset, text, value):
        if value:
            return queryset.filter(text__isnull=True)
        else:
            return queryset.filter(text__isnull=False)



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
            "password": "1234"
        }

        serializer = TokenSerializer(data=user_data)
        if serializer.is_valid():
            return Response(serializer.data, status=200)
        else:
            print(serializer.errors)
        return Response("Kakao Login False", status=400)


# /memos
class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all().order_by('-created_at')
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filter_class = MemoFilter
