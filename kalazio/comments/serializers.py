from rest_framework import serializers

from product.models import SpicialField, SpicialFieldValue
from .models import Comment, Rate, LikeComment, DisLikeComment, GoodPoint, WeakPoint
from product.serializers import ProductSerializerForComments, SpicialFieldSerializer


class RateSerializer(serializers.ModelSerializer):
    spicialField = serializers.SerializerMethodField()

    class Meta:
        model = Rate
        exclude = ('user',)

    def get_spicialField(self, obj):
        return {
            'key': obj.spicialField.spicialField.spicialField.key,
            'value': obj.spicialField.spicialField.value
        }


class LikeCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikeComment
        exclude = ('user',)


class DisLikeCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisLikeComment
        exclude = ('user',)


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    suggest = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    detailRate = serializers.SerializerMethodField()
    goodPoint = serializers.SerializerMethodField()
    weakPoint = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('user',
                  'detailRate',
                  'goodPoint',
                  'weakPoint',
                  'title',
                  'content',
                  'suggest',
                  'point',
                  'date',
                  'name',)

    def get_user(self, obj):
        if obj.user.first_name:
            return obj.user.first_name + ' ' + obj.user.last_name
        return None

    def get_goodPoint(self, obj):
        list=[]
        g = GoodPoint.objects.filter(comment=obj)
        for i in g :
            list.append(i.good_text)
        return list

    def get_weakPoint(self, obj):
        list=[]
        w = WeakPoint.objects.filter(comment=obj)
        for i in w :
            list.append(i.weak_text)
        return list

    def get_name(self, obj):
        if obj.show:
            return 'مشخصات مخفی'
        return f'{obj.user.first_name} {obj.user.last_name}'

    def get_suggest(self, obj):
        return obj.get_suggest()

    def get_detailRate(self, obj):
        list = []
        for detail in obj.detailRate.all():
            list.append(detail)
        serializer = RateSerializer(list, many=True)
        return serializer.data


class CommentSerializerForList(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    suggest = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    detailRate = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('user',
                  'detailRate',
                  'title',
                  'content',
                  'suggest',
                  'image',
                  'point',
                  'date',
                  'name',
                  'seller')

    def get_name(self, obj):
        if obj.show:
            return 'مشخصات مخفی'
        return f'{obj.user.first_name} {obj.user.last_name}'

    def get_image(self, obj):
        return obj.product.get_absolute_url()

    def get_suggest(self, obj):
        return obj.get_suggest()

    def get_detailRate(self, obj):
        list = []
        for detail in obj.detailRate.all():
            list.append(detail)
        serializer = RateSerializer(list, many=True)
        return serializer.data

    def get_seller(self, obj):
        return obj.product.seller.title


class CommentSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = ('confirm', 'detailRate', 'user')
