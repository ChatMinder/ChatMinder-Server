from django.db import models
from django.db.models import Model


class BaseModel(Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class Memo(BaseModel):
    memotext = models.TextField(null=True, blank=True)
    is_marked = models.BooleanField(default=False)

    class Meta:
        db_table = 'memo'


class Image(BaseModel):
    memo = models.OneToOneField(Memo, on_delete=models.CASCADE)
    image_file = models.ImageField(upload_to="file")

    def __str__(self):
        return self.memo.pk

    class Meta:
        db_table = 'image'


class Link(BaseModel):
    memo = models.OneToOneField(Memo, on_delete=models.CASCADE)
    link = models.URLField()

    class Meta:
        db_table = 'link'

