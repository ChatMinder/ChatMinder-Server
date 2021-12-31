from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from app.models import Memo
from app.serializers_memo import MemoSerializer


class MemoFilter(FilterSet):
    memo_text = filters.CharFilter(field_name='memo_text', lookup_expr="icontains")
    is_marked = filters.BooleanFilter(field_name='is_marked')
    image_null = filters.BooleanFilter(field_name='image', method='is_image_null')
    link_null = filters.BooleanFilter(field_name='link', method='is_link_null')

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


class MemoViewSet(ModelViewSet):
    queryset = Memo.objects.all().order_by('-created_at')
    serializer_class = MemoSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filter_class = MemoFilter

