from django.urls import include, path
from rest_framework import routers

from app.views import *

router = routers.DefaultRouter()
router.register(r'memos', MemoViewSet)

urlpatterns = router.urls
