from rest_framework import serializers
from .models import Notifications, User, Gift


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ('user', 'title', 'date', 'content', 'get_level')


class GiftSerializerForOrder(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = ('serial',)


class GiftSerializerForList(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    codeMelli = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ('password',)

    def get_codeMelli(self, obj):
        return obj.codeMelli if obj.codeMelli else ''


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email',
                  'phone',
                  'codeMelli',
                  'newsletters',
                  'first_name',
                  'last_name',
                  'gender',
                  'melliImage',
                  'dateOfBirth',
                  'address',
                  'ibanNumber',
                  'cartNumber'
                  )
