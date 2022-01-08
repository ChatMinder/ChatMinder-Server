import json
from itertools import chain

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

from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.pagination import PaginationHandlerMixin
from app.serializers import TokenSerializer, MemoSerializer, UserSerializer, ImageSerializer, TagSerializer
from app.models import User, Memo, Tag, Image
from app.storages import s3_upload_image, s3_delete_image
from app.exceptions import *

from server.settings.base import env


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


def get_extension(image_name):
    splited_name = image_name.split('.')
    return '.' + splited_name[len(splited_name) - 1]


def get_resource_url(user, hash, extension):
    return user.kakao_id + '/' + hash + extension


def get_filename(hash, extension):
    return hash + extension


def get_image_data(user_id, memo_id, resource_url, filename):
    return {
        "user": user_id,
        "memo": memo_id,
        "url": resource_url,
        "name": filename
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
            return Response({"message": "로그인 성공", "data": serializer.data}, status=200)
        else:
            print(serializer.errors)
        return JsonResponse({"message": "로그인 실패"}, status=400)


# /images
class ImagesView(APIView):
    def get(self, request):
        try:
            user_authenticate(request)
            image_id = request.GET.get('id', None)
            many = False
            if image_id is None:
                many = True
                image = Image.objects.filter(user=request.user)
            else:
                image = get_object_or_404(Image, pk=image_id)
                ownership_check(request.user, image.user)
            image_data = ImageSerializer(image, many=many).data
            return JsonResponse({"message": "이미지 조회 성공", "data": image_data}, status=200)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)

    def post(self, request):
        try:
            user_authenticate(request)
            user = request.user
            size = int(request.data['size'])
            memo_id = request.data['memo_id']
            ret = []
            for index in range(size):
                hash = get_random_hash(length=30)
                image_name = "image" + str(index)
                image_file = request.FILES[image_name]
                extension = get_extension(image_file.name)
                resource_url = get_resource_url(user, hash, extension)
                filename = get_filename(hash, extension)
                image_data = get_image_data(user.id, memo_id, resource_url, filename)
                serializer = ImageSerializer(data=image_data)
                if serializer.is_valid():
                    serializer.save()
                    s3_upload_image(image_file, resource_url)
                    ret.append(serializer.data)
                else:
                    return Response(serializer.errors, status=400)
            return JsonResponse({"message": "이미지 업로드 성공", "data": ret}, status=200)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)

    def delete(self, request):
        try:
            user_authenticate(request)
            image_id = request.GET.get('id', None)
            image = get_object_or_404(Image, pk=image_id)
            ownership_check(request.user, image.user)
            image.delete()
            s3_delete_image(image)
            return JsonResponse({"message": "이미지 삭제 성공"}, status=200)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)


class BookmarkView(APIView, PaginationHandlerMixin):
    pagination_class = PageNumberPagination

    def get_memos(self, pk):
        return get_object_or_404(Memo, pk=pk)

    def post(self, request):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        memo = Memo.objects.get(id=request.data['memo'], user=user)
        print(memo)
        if request.data['is_marked']:
            memo.is_marked = True
        else:
            memo.is_marked = False
        memo.save()
        memos = Memo.objects.filter(user=user).order_by('-created_at')
        page = self.paginate_queryset(memos)
        if page is not None:
            serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
        else:
            serializer = MemoSerializer(memos, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)


class MemoList(APIView, PaginationHandlerMixin):
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        try:
            user_authenticate(request)
            memos = Memo.objects.filter(user=request.user).order_by('-created_at')
            page = self.paginate_queryset(memos)
            if page is not None:
                serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
            else:
                serializer = MemoSerializer(memos, many=True)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)

    def post(self, request, *args, **kwargs):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        serializer = MemoSerializer(data=request.data)
        if serializer.is_valid():
            if request.data['is_tag_new']:
                try:  # DB에 중복값이 있다면 저장안함
                    tag = Tag.objects.get(tag_name=request.data['tag_name'])
                except Tag.DoesNotExist:
                    tag = Tag.objects.create(tag_name=request.data['tag_name'], tag_color=request.data['tag_color'],
                                             user=user)
                Memo.objects.create(memo_text=request.data['memo_text'], url=request.data['url'], tag=tag, user=user)
                memos = Memo.objects.filter(user=user).order_by('-created_at')
                page = self.paginate_queryset(memos)
                if page is not None:
                    serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
                else:
                    serializer = MemoSerializer(memos, many=True)
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            else:
                try:
                    tag = Tag.objects.get(id=request.data['tag'])
                except Tag.DoesNotExist:
                    tag = None
                Memo.objects.create(memo_text=request.data['memo_text'], url=request.data['url'], tag=tag, user=user)
                memos = Memo.objects.filter(user=user).order_by('-created_at')
                page = self.paginate_queryset(memos)
                if page is not None:
                    serializer = self.get_paginated_response(MemoSerializer(page, many=True).data)
                else:
                    serializer = MemoSerializer(memos, many=True)
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemoDetial(APIView):
    def get_memos(self, pk):
        return get_object_or_404(Memo, pk=pk)

    def patch(self, request, pk):
        try:
            user_authenticate(request)
            memo = self.get_memos(pk)
            ownership_check(request.user, memo.user)
            serializer = MemoSerializer(memo, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(serializer.errors, tatus=status.HTTP_400_BAD_REQUEST)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)

    def delete(self, request, pk):
        try:
            user_authenticate(request)
            memo = self.get_memos(pk)
            ownership_check(request.user, memo.user)
            memo.delete()
            return JsonResponse({"message": "메모 삭제 성공"}, status=status.HTTP_200_OK)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)


class MemoFilterViewSet(ModelViewSet):
    queryset = Memo.objects.all()
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination

    @action(detail=False)
    def texts(self, request, *args, **kwargs):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        queryset = Memo.objects.filter(memo_text__isnull=False, user=user).order_by('-created_at')
        self.paginator.page_size_query_param = "page_size"
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    @action(detail=False)
    def links(self, request, *args, **kwargs):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        queryset = Memo.objects.filter(url__isnull=False, user=user).order_by('-created_at')
        self.paginator.page_size_query_param = "page_size"
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    @action(detail=True)
    def tags(self, request, pk):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        queryset = Memo.objects.filter(tag_id=pk, user=user).order_by('-created_at')
        self.paginator.page_size_query_param = "page_size"
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    # @action(detail=False)
    # def images(self, request, *args, **kwargs):
    #     user = request.user
    #     if request.user.is_anonymous:
    #         return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
    #     images_data = Image.objects.all()
    #     for i in images_data:
    #         print(i+1)
    #         a = Memo.objects.filter(id=i.memo_id).order_by('-created_at')
    #         b =Memo.objects.filter(id=(i+1).memo_id).order_by('-created_at')
    #         queryset = list(chain(a,b))
    #         print(queryset)
    #     self.paginator.page_size_query_param = "page_size"
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     serializer = self.get_serializer(queryset, many=True)
    #     return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


class TagList(APIView):

    def get(self, request):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        tags = Tag.objects.filter(user=user).order_by('-created_at')
        serializer = TagSerializer(tags, many=True, context={'user': request.user})
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    def post(self, request):
        user = request.user
        if request.user.is_anonymous:
            return JsonResponse({'message': '알 수 없는 유저입니다.'}, status=404)
        Tag.objects.create(user=user, tag_name=request.data['tag_name'], tag_color=request.data['tag_color'])
        tags = Tag.objects.filter(user=user).order_by('-created_at')
        serializer = TagSerializer(tags, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED, safe=False)


class TagDetail(APIView):
    def get_tag(self, pk):
        return get_object_or_404(Tag, pk=pk)

    def patch(self, request, pk):
        try:
            user_authenticate(request)
            tag = self.get_tag(pk)
            ownership_check(request.user, tag.user)
            serializer = TagSerializer(tag, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(serializer.errors, tatus=status.HTTP_400_BAD_REQUEST)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)


    def delete(self, request, pk):
        try:
            user_authenticate(request)
            tag = self.get_tag(pk)
            ownership_check(request.user, tag.user)
            tag.delete()
            return JsonResponse({"message": "태그 삭제 성공"}, status=status.HTTP_200_OK)
        except UserIsAnonymous:
            return JsonResponse({"message": "알 수 없는 유저입니다."}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "권한이 없습니다."}, status=400)

    def delete(self, request, pk):
        tags = self.get_tag(pk)
        tags.delete()
        return JsonResponse({'message': '삭제 완료'}, status=status.HTTP_200_OK)
