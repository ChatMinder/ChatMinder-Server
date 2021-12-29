from django.urls import include, path

from app.views import HelloView, KakaoLoginView

urlpatterns = [
    path('hello', HelloView.as_view()),
    path('auth/kakao', KakaoLoginView.as_view())
]