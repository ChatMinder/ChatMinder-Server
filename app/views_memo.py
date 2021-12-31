from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.models import Memo
from app.serializers_memo import MemoSerializer



class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all().order_by('-created_at')
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination


