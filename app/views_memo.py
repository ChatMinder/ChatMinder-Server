from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.serializer import *


class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all().order_by('-created_at')
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination

