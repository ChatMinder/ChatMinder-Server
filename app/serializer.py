from rest_framework import serializers

from app.models import *


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'


class MemoSerializer(serializers.ModelSerializer):
    memo_link = LinkSerializer(read_only=True)
    memo_image = ImageSerializer(read_only=True)
    tag_name = serializers.SerializerMethodField()

    class Meta:
        model = Memo
        fields = ['memo_text', 'is_marked', 'memo_link', 'memo_image', 'tag_name']

    def get_tag_name(self, obj):
        return obj.tag_id.tag_name
