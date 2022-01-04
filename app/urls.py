from django.urls import include, path
from rest_framework import routers

from app.views import HelloView, KakaoLoginView, ImagesView, UserView
from app.views import MemoViewSet

router = routers.DefaultRouter()
router.register(r'memos', MemoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view()),
    path('images', ImagesView.as_view()),
    path('users', UserView.as_view()),
]