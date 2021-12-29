from django.urls import include, path

from app.views import *

urlpatterns = [
    path('hello', HelloView.as_view()),
    path('memos', MemoListView.as_view()),
    path('memos/<int:pk>', MemoDetailView.as_view())
]