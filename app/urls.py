from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from app.views import HelloView, KakaoLoginView, ImagesView, UserView, MemoText, MemoLink, BookmarkView
from app.views import MemoList, MemoDetial
from server.settings import base

router = routers.DefaultRouter()
router.register(r'texts', MemoText)
router.register(r'links', MemoLink)


urlpatterns = [
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view()),
    path('memos', MemoList.as_view()),
    path('memos/<int:pk>', MemoDetial.as_view()),
    path('memos/bookmark', BookmarkView.as_view()),
    path('memos/', include(router.urls)),
    path('images', ImagesView.as_view()),
    path('users', UserView.as_view()),
] + static(base.MEDIA_URL, document_root=base.MEDIA_ROOT)

