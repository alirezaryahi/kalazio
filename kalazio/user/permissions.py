from rest_framework import generics, mixins, permissions


class UserIsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id