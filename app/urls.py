from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from app.views import HelloView, KakaoLoginView
from app.views import MemoList, MemoDetial
from server.settings import base


urlpatterns = [
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view()),
    path('memos', MemoList.as_view()),
    path('memos/<int:pk>', MemoDetial.as_view())
] + static(base.MEDIA_URL, document_root=base.MEDIA_ROOT)
