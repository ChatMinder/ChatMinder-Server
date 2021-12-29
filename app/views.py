from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from app.serializer import *


class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all()
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination


"""
class MemoListView(APIView):
    pagination_class = PageNumberPagination

    def get(self, request):
        memos = Memo.objects.all()
        serializer = MemoSerializer(memos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MemoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemoDetailView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Memo, pk=pk)

    def get(self, request, pk):
        memo = self.get_object(pk)
        serializer = MemoSerializer(memo)
        return Response(serializer.data)

    def patch(self, request, pk):
        memo = self.get_object(pk)
        serializer = MemoSerializer(memo)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        memo = self.get_object(pk)
        memo.delete()
        return Response("삭제 완료", status=status.HTTP_200_OK)


"""
