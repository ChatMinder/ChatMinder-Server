from django.db.models import Model
from django.db import models

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager


class BaseModel(Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    kakao_id = models.CharField(max_length=20, unique=True, null=False, blank=False)
    kakao_email = models.EmailField(null=True)
    password = models.CharField(max_length=200, null=True, blank=True, default="")
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    nickname = models.CharField(max_length=20, null=False, blank=False, default="anonymous")

    USERNAME_FIELD = 'kakao_id'
    REQUIRED_FIELDS = ['kakao_email', 'nickname']

    objects = UserManager()

    class Meta:
        db_table = 'user'


class Tag(BaseModel):
    COLOR_IN_TAG_CHOICES = [
        ('#5DA7EF', '#5DA7EF'),
        ('#9ECBFF', '#9ECBFF'),
        ('#C8D769', '#C8D769'),
        ('#50B093', '#50B093'),
        ('#81C7BA', '#81C7BA'),
        ('#B282CC', '#B282CC'),
        ('#F85C5D', '#F85C5D'),
        ('#FFAB41', '#FFAB41'),
        ('#FA7931', '#FA7931'),
        ('#FFD84E', '#FFD84E'),
    ]

    tag_name = models.CharField(max_length=20, null=True, blank=True)
    tag_color = models.CharField(max_length=10, choices=COLOR_IN_TAG_CHOICES, null=True, blank=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'tag'


class Memo(BaseModel):
    memo_text = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    is_marked = models.BooleanField(default=False)
    timestamp = models.CharField(max_length=50)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, null=True, blank=True, related_name='memo_tag')
    user = models.ForeignKey('User', on_delete=models.CASCADE,  null=True, related_name='memo_user')
    has_image = models.BooleanField(default=False)

    class Meta:
        db_table = 'memo'


class Image(BaseModel):
    url = models.CharField(null=False, blank=False, default="url", max_length=50)
    name = models.CharField(null=False, blank=False, max_length=40, default="anonymous")
    memo = models.ForeignKey('Memo', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'image'


class Schedule(Model):
    start_date = models.DateTimeField(editable=True)
    end_date = models.DateTimeField(editable=True)
    is_repeated = models.BooleanField(default=False)
    memo = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'schedule'
