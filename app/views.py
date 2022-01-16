import json
from itertools import chain

from django.db.models import Q

import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import status
import string
import random

from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ParseError

from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.pagination import PaginationHandlerMixin
from app.serializers import *
from app.models import User, Memo, Tag, Image
from app.storages import s3_upload_image, s3_delete_image
from app.exceptions import *
from app.mixins import *

from server.settings.base import env


def validate_kakao_response(kakao_response):
    kakao_id = kakao_response.get('id', None)
    kakao_account = kakao_response.get('kakao_account', None)
    kakao_profile = kakao_account.get('profile', None)
    kakao_nickname = kakao_profile.get('nickname', None)
    if kakao_id is None or kakao_account is None \
            or kakao_profile is None or kakao_nickname is None:
        raise KakaoResponseError


def get_random_hash(length):
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(length):
        result += random.choice(string_pool)
    return result


def user_authenticate(request):
    if request.user.is_anonymous:
        raise UserIsAnonymous


def ownership_check(user1, user2):
    if user1 != user2:
        raise UserIsNotOwner


def size_check(size):
    if int(size) <= 0:
        raise SizeIntegerError


def set_has_image_true(memo_id):
    memo = get_object_or_404(Memo, pk=memo_id)
    memo.has_image = True
    memo.save()


def set_has_image_false(memo_id):
    memo = get_object_or_404(Memo, pk=memo_id)
    memo.has_image = False
    memo.save()


def get_extension(image_name):
    splited_name = image_name.split('.')
    return '.' + splited_name[len(splited_name) - 1]


def get_resource_url(user, hash, extension):
    return user.kakao_id + '/' + hash + extension


def get_filename(hash, extension):
    return hash + extension


def param_exists(request, param):
    param = request.GET.get(param, 'false')
    if param == 'false':
        return False
    return True


def get_image_data(request, index):
    hash = get_random_hash(length=30)
    memo_id = request.data.get('memo_id', -1)
    image_key = "image" + str(index)
    image_file = request.FILES[image_key]
    image_name = image_file.name
    extension = get_extension(image_name)
    return {
        "user": request.user.id,
        "memo": memo_id,
        "url": get_resource_url(request.user, hash, extension),
        "name": get_filename(hash, extension),
        "file": image_file
    }


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
        try:
            user_authenticate(request)
            serializer = UserSerializer(request.user)
            return JsonResponse(serializer.data, status=200)
        except UserIsAnonymous:
            return Response("알 수 없는 유저입니다.", status=404)

    # for debug
    def post(self, request):
        data = JSONParser().parse(request)
        user_data = {
            "kakao_id": data.get('kakao_id', None),
            "kakao_email": data.get('kakao_email', None),
            "nickname": data.get('nickname', None)
        }
        serializer = TokenSerializer(data=user_data)
        if serializer.is_valid():
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


# /auth/token
class TokenView(UserAuthMixin, APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        data = {
            "refresh": data['refresh_token']
        }
        serializer = TokenRefreshSerializer(data=data)
        if serializer.is_valid():
            return JsonResponse({"status": 201, "refresh_token": serializer.data['refresh'],
                                 "access_token": serializer.data['access']}, status=201)


# /auth/kakao
class KakaoLoginView(UserAuthMixin, APIView):
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

        validate_kakao_response(kakao_response)

        kakao_id = str(kakao_response.get('id'))
        kakao_account = kakao_response.get('kakao_account')

        kakao_email = kakao_account.get('email', None)
        nickname = kakao_account.get('profile', None).get('nickname', None)

        user_data = {
            "kakao_id": kakao_id,
            "kakao_email": kakao_email,
            "nickname": nickname,
        }

        serializer = TokenSerializer(data=user_data)
        if serializer.is_valid():
            return Response({"message": "로그인 성공", "status": 200, "refresh_token": serializer.data['refresh'],
                             "access_token": serializer.data['access']}, status=200)
        else:
            print(serializer.errors)
        return JsonResponse({"message": "CHATMINDER_SERVER_ERROR", "status": "400"}, status=400)


# /images
class ImagesView(UserAuthMixin, APIView):
    # 유저가 가진 모든 이미지 조회
    def get(self, request):
        user_authenticate(request)
        image = Image.objects.filter(user=request.user)
        serializer = ImageSerializer(image, many=True)
        return JsonResponse({"message": "이미지 조회 성공", "data": serializer.data}, status=200)

    def post(self, request):
        try:
            user_authenticate(request)
            size = int(request.data.get('size', -1))
            memo_id = int(request.data.get('memo_id', -1))
            size_check(size)
            set_has_image_true(memo_id)
            ret = []
            for index in range(size):
                image_data = get_image_data(request, index)
                serializer = ImageSerializer(data=image_data)
                if serializer.is_valid():
                    serializer.save()
                    s3_upload_image(image_data.get('file', None), image_data.get('url', None))
                    ret.append(serializer.data)
                else:
                    return Response(serializer.errors, status=400)
            return JsonResponse({"message": "이미지 업로드 성공", "data": ret}, status=201)
        except SizeIntegerError:
            return JsonResponse({"message": "Size가 정수가 아니거나, 1보다 작은 수 입니다."}, status=400)
        except KeyError:
            return JsonResponse({"message": "값이 유효하지 않습니다."}, status=400)

    def delete(self, request):
        user_authenticate(request)
        image_id = request.GET.get('id', None)
        image = get_object_or_404(Image, pk=image_id)
        ownership_check(request.user, image.user)
        set_has_image_false(image.memo.id)
        image.delete()
        s3_delete_image(image)
        return JsonResponse({"message": "이미지 삭제 성공"}, status=200)


class ImageDetailView(UserAuthMixin, APIView):
    def get(self, request, pk):
        # try:
        user_authenticate(request)
        image_id = pk
        many = False
        if image_id is None:
            many = True
            image = Image.objects.filter(user=request.user)
        else:
            image = get_object_or_404(Image, pk=image_id)
            ownership_check(request.user, image.user)
        image_data = ImageSerializer(image, many=many).data
        return JsonResponse({"message": "이미지 조회 성공", "data": image_data}, status=200)


# /memos/images
class MemoImageFilter(UserAuthMixin, APIView):
    def get(self, request):
        user_authenticate(request)
        queryset = Memo.objects.filter(user=request.user, has_image=True).order_by('created_at')
        serializer = MemoSerializer(queryset, many=True)
        return JsonResponse(serializer.data, status=200, safe=False)


# /memos/bookmark
class BookmarkView(APIView):
    # pagination_class = PageNumberPagination

    def get_memos(self, pk):
        return get_object_or_404(Memo, pk=pk)

    def post(self, request):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        memo = Memo.objects.get(id=request.data['memo_id'], user=user)
        if request.data['is_marked']:
            memo.is_marked = False
        else:
            memo.is_marked = True
        memo.save()
        # memos = Memo.objects.filter(user=user).order_by('-created_at')
        # page = self.paginate_queryset(memos)
        # if page is not None:
        #     serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
        # else:
        serializer = MemoSerializer(memo)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)


# /memos
class MemoList(UserAuthMixin, APIView, PaginationHandlerMixin):
    # pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        user_authenticate(request)
        memos = Memo.objects.filter(user=request.user).order_by('created_at')
        # page = self.paginate_queryset(memos)
        # if page is not None:
        #     serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
        # else:
        serializer = MemoSerializer(memos, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_authenticate(request)
        tag_id = request.data.get('tag_id', None)
        tag_name = request.data.get('tag_name', None)
        tag_color = request.data.get('tag_color', None)
        if (tag_id is None) and (tag_name is not None) and (tag_color is not None):
            tag, flag = Tag.objects.get_or_create(tag_name=tag_name,
                                                  tag_color=tag_color,
                                                  user=user)
            memo = Memo.objects.create(memo_text=request.data.get('memo_text', None),
                                       url=request.data.get('url', None),
                                       timestamp=request.data.get('timestamp', None),
                                       tag=tag, user=user)
            tags_data = TagSerializer(tag).data
            # memo = Memo.objects.filter(user=user).order_by('-created_at')
            # page = self.paginate_queryset(memos)
            # if page is not None:
            # serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
            # else:
            memos_data = MemoSerializer(memo).data
            return JsonResponse({"tag": tags_data, "memo": memos_data}, status=status.HTTP_201_CREATED, safe=False)
        else:
            try:
                tag = Tag.objects.get(id=tag_id, user=user)
            except Tag.DoesNotExist:
                tag = None
            memo = Memo.objects.create(memo_text=request.data.get('memo_text', None),
                                       url=request.data.get('url', None),
                                       timestamp=request.data.get('timestamp', None),
                                       tag=tag, user=user)
            # page = self.paginate_queryset(memos)
            # if page is not None:
            #     serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
            # else:
            serializer = MemoSerializer(memo)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, safe=False)


# /memos/<int:pk>
class MemoDetail(UserAuthMixin, APIView):
    def get_memos(self, pk):
        return get_object_or_404(Memo, pk=pk)

    def patch(self, request, pk):
        user_authenticate(request)
        memo = self.get_memos(pk)
        ownership_check(request.user, memo.user)
        serializer = MemoSerializer(memo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, tatus=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user_authenticate(request)
        memo = self.get_memos(pk)
        ownership_check(request.user, memo.user)
        memo.delete()
        return JsonResponse({"message": "메모 삭제 성공"}, status=status.HTTP_200_OK)


# /memos/texts
class MemoTextFilter(UserAuthMixin, APIView):

    def get(self, request, *args, **kwargs):
        user_authenticate(request)
        user = request.user
        queryset = Memo.objects.filter(memo_text__isnull=False, url__isnull=True, has_image=False, user=user).order_by(
            'created_at')
        # self.paginator.page_size_query_param = "page_size"
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = MemoSerializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


# /memos/links
class MemoLinkFilter(UserAuthMixin, APIView):

    def get(self, request, *args, **kwargs):
        user_authenticate(request)
        user = request.user
        queryset = Memo.objects.filter(url__isnull=False, user=user).order_by('created_at')
        # self.paginator.page_size_query_param = "page_size"
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = MemoLinkSerializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


# /tags/<int:pk>/memos
class MemoTagFilter(UserAuthMixin, APIView):

    def get(self, request, pk):
        user_authenticate(request)
        user = request.user
        queryset = Memo.objects.filter(tag_id=pk, user=user).order_by('created_at')
        # self.paginator.page_size_query_param = "page_size"
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = MemoSerializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


# /tags
class TagList(UserAuthMixin, APIView):

    def get(self, request):
        user_authenticate(request)
        user = request.user
        tags = Tag.objects.filter(user=user).order_by('created_at')
        serializer = TagSerializer(tags, many=True, context={'user': request.user})
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    def post(self, request):
        user_authenticate(request)
        user = request.user
        tag = Tag.objects.create(user=user, tag_name=request.data['tag_name'], tag_color=request.data['tag_color'])
        serializer = TagSerializer(tag)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, safe=False)


# /tags/<int:pk>
class TagDetail(UserAuthMixin, APIView):
    def get_tag(self, pk):
        return get_object_or_404(Tag, pk=pk)

    def get(self, request, pk):
        user_authenticate(request)
        tag = self.get_tag(pk)
        ownership_check(request.user, tag.user)

        has_image = param_exists(request, 'image')
        has_link = param_exists(request, 'link')
        has_text = param_exists(request, 'text')
        is_marked = param_exists(request, 'mark')

        fields = ['id', 'tag_id', 'tag_name', 'tag_color', 'is_marked', 'timestamp']

        tag_id = pk
        if tag_id is None:
            return JsonResponse({"message": "tag id error"}, status=400)

        # 아무것도 선택되지 않았을 때
        if (has_image or has_link or has_text or is_marked) is False:
            return JsonResponse({"data": []})

        q = Q()
        if has_image:
            q |= Q(tag_id=tag_id, has_image=has_image)
            fields.append('images')

        if has_link:
            q |= Q(tag_id=tag_id, url__isnull=False)
            fields.append('url')

        if has_text:
            q |= Q(tag_id=tag_id, memo_text__isnull=False)
            fields.append('memo_text')

        if is_marked:
            q &= Q(tag_id=tag_id, is_marked=True)
        else:
            q &= Q(tag_id=tag_id)

        filteredMemos = Memo.objects.filter(q).distinct()
        serializer = MemoSerializer(filteredMemos, many=True, fields=tuple(fields))
        return JsonResponse({"message": "메모 필터링 성공", "data": serializer.data})

    def patch(self, request, pk):
        user_authenticate(request)
        tag = self.get_tag(pk)
        ownership_check(request.user, tag.user)
        serializer = TagSerializer(tag, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, tatus=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user_authenticate(request)
        tag = self.get_tag(pk)
        ownership_check(request.user, tag.user)
        tag.delete()
        return JsonResponse({"message": "태그 삭제 성공"}, status=status.HTTP_200_OK)


# /memos/tags
class MemoTag(UserAuthMixin, APIView):

    def post(self, request):
        user_authenticate(request)
        memo_id = request.data.get('memo_id', None)
        tag_id = request.data.get('tag_id', None)
        memo = Memo.objects.get(id=memo_id)
        ownership_check(request.user, memo.user)
        memo.tag_id = tag_id
        memo.save()
        serializer = MemoSerializer(memo)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, safe=False)
