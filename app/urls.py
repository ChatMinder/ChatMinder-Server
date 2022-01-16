from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from app.views import HelloView, KakaoLoginView, ImagesView, UserView, BookmarkView, TagList, TagDetail, MemoTextFilter, \
    MemoLinkFilter, MemoTagFilter, TokenView, MemoImageFilter

from app.views import MemoList, MemoDetail
from server.settings import base

urlpatterns = [
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view()),
    path('auth/token', TokenView.as_view()),
    path('memos', MemoList.as_view()),
    path('memos/<int:pk>', MemoDetail.as_view()),
    path('memos/bookmark', BookmarkView.as_view()),
    path('memos/texts', MemoTextFilter.as_view()),
    path('memos/links', MemoLinkFilter.as_view()),
    path('memos/images', MemoImageFilter.as_view()),
    path('tags/<int:pk>/memos', MemoTagFilter.as_view()),
    path('images', ImagesView.as_view()),
    path('users', UserView.as_view()),
    path('tags', TagList.as_view()),
    path('tags/<int:pk>', TagDetail.as_view())
] + static(base.MEDIA_URL, document_root=base.MEDIA_ROOT)

