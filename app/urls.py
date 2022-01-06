from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from app.views import HelloView, KakaoLoginView, ImagesView, UserView, BookmarkView, MemoFilterViewSet


from app.views import MemoList, MemoDetial
from server.settings import base

router = routers.DefaultRouter()
router.register(r'memos', MemoFilterViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view()),
    path('memos', MemoList.as_view()),
    path('memos/<int:pk>', MemoDetial.as_view()),
    path('memos/bookmark', BookmarkView.as_view()),
    path('images', ImagesView.as_view()),
    path('users', UserView.as_view()),
] + static(base.MEDIA_URL, document_root=base.MEDIA_ROOT)

