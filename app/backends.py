from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AnonymousUser

UserModel = get_user_model()


class KakaoBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, is_kakao=None, **kwargs):
        print("###")
        print(username)
        print(password)
        print(is_kakao)
        print("###")
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            pass
        else:
            if is_kakao is True:
                if self.user_can_authenticate(user):
                    return user
            else:
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
