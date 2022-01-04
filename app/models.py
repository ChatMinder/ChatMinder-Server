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
    kakao_email = models.EmailField(unique=True, null=False, blank=False)
    password = models.CharField(max_length=20, null=True, blank=True, default="")
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
        ('RD', 'red'),
        ('GR', 'green'),
        ('BL', 'blue'),
        # 더 추가해야됨!
    ]

    tag_name = models.CharField(max_length=20, null=False, blank=False)
    tag_color = models.CharField(max_length=2, choices=COLOR_IN_TAG_CHOICES)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'tag'


class Memo(BaseModel):
    memo_text = models.TextField(null=True)
    is_marked = models.BooleanField(default=False)
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'memo'


class Link(BaseModel):
    url = models.URLField(null=False, blank=False)
    memo = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'link'


class Image(BaseModel):
    image = models.ImageField(null=False, blank=False)
    memo = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'image'


class Schedule(Model):
    start_date = models.DateTimeField(editable=True)
    end_date = models.DateTimeField(editable=True)
    is_repeated = models.BooleanField(default=False)
    memo = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'schedule'
