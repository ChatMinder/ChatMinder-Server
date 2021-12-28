from django.urls import include, path

from app.views import HelloView

urlpatterns = [
    path('hello', HelloView.as_view()),
]