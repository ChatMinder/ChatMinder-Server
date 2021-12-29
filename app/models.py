from django.db.models import Model
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin


class BaseModel(Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    kakao_id = models.CharField(max_length=40, unique=True, null=False, blank=False)
    kakao_email = models.EmailField(unique=True, null=False, blank=False)
    is_superuser = models.BooleanField(default=False)
    nickname = models.CharField(max_length=20, null=False, blank=False, default="anonymous")

    USERNAME_FIELD = 'kakao_id'
    REQUIRED_FIELDS = ['kakao_email', 'nickname']

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
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'tag'


class Memo(BaseModel):
    memo_text = models.TextField(null=False)
    is_marked = models.BooleanField(default=False)
    tag_id = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'memo'


class Link(BaseModel):
    url = models.URLField(null=False, blank=False)
    memo_id = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'link'


class Image(BaseModel):
    image = models.ImageField(null=False, blank=False)
    memo_id = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'image'


class Schedule(Model):
    start_date = models.DateTimeField(editable=True)
    end_date = models.DateTimeField(editable=True)
    is_repeated = models.BooleanField(default=False)
    memo_id = models.ForeignKey('Memo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'schedule'
