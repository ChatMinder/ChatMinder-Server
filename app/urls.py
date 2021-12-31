from django.urls import include, path
from rest_framework import routers

from app.views import *
from app.views_memo import MemoViewSet

router = routers.DefaultRouter()
router.register(r'memos', MemoViewSet)

urlpatterns = router.urls
