from rest_framework import permissions

class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Zezwala na edycję (PUT/PATCH) i usuwanie (DELETE) tylko autorowi obiektu lub administratorowi.
    Bezpieczne metody odczytu (GET, HEAD, OPTIONS) są dozwolone dla każdego.
    """
    def has_object_permission(self, request, view, obj):
        # Odczyt dozwolony zawsze
        if request.method in permissions.SAFE_METHODS:
            return True

        # Zezwól, jeśli użytkownik to autor posta/komentarza ALBO jest administratorem (is_staff)
        return obj.author == request.user or request.user.is_staff