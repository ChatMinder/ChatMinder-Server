from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ParseError

from app.exceptions import *


class UserAuthMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except UserIsAnonymous:
            return JsonResponse({"message": "ANONYMOUS_USER_ERROR"}, status=404)
        except UserIsNotOwner:
            return JsonResponse({"message": "USER_PERMISSION_DENIED"}, status=400)
        except TokenError:
            return JsonResponse({"message": "TOKEN_IS_EXPIRED_OR_INVALID"}, status=401)
        except KakaoResponseError:
            return JsonResponse({"message": "KAKAO_SERVER_ERROR"}, status=500)
