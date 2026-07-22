from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Dynamicznie pobierz właściciela: 'author' dla postów, 'creator' dla zadań
        owner = getattr(obj, 'author', None) or getattr(obj, 'creator', None)

        return owner == request.user or request.user.is_staff