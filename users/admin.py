from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SharedImage, Notification, UserRelationship


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """ Rozbudowany widok gracza w panelu administracyjnym """

    # Kolumny widoczne na głównej liście użytkowników
    list_display = ('username', 'email', 'level', 'dobroty', 'is_verified', 'last_active', 'is_staff')

    # Filtry boczne - idealne do szybkiego szukania np. tylko zweryfikowanych graczy
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active', 'level')

    # Wyszukiwarka na górze listy
    search_fields = ('username', 'email')

    # Zabezpieczenie pól, które powinny być tylko do odczytu dla admina
    readonly_fields = ('last_active', 'last_login', 'date_joined')

    # Podział pól na logiczne sekcje w widoku edycji profilu
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informacje Osobiste', {
            'fields': ('first_name', 'last_name', 'email', 'avatar', 'bio', 'is_verified')
        }),
        ('Statystyki i RPG', {
            'fields': ('level', 'experience', 'skill_points', 'dobroty', 'reputation', 'skills')
        }),
        ('Gildia', {
            'fields': ('guild', 'guild_role')
        }),
        ('Aktywność', {
            'fields': ('last_active', 'last_daily_reward')
        }),
        ('Uprawnienia', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Ważne Daty', {
            'fields': ('last_login', 'date_joined')
        }),
    )


@admin.register(UserRelationship)
class UserRelationshipAdmin(admin.ModelAdmin):
    """ Widok do podglądu znajomości i blokad między graczami """
    list_display = ('from_user', 'status', 'to_user', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')

    # Admin nie powinien ręcznie edytować daty utworzenia relacji
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """ Zarządzanie systemem powiadomień (Push/In-app) """
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')

    # Szybka akcja dla admina do masowego oznaczania powiadomień jako przeczytane
    actions = ['mark_as_read']

    @admin.action(description="Oznacz wybrane jako przeczytane")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)


@admin.register(SharedImage)
class SharedImageAdmin(admin.ModelAdmin):
    """ Podgląd wszystkich plików multimedialnych wgranych przez graczy """
    list_display = ('id', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('uploaded_by__username',)
    readonly_fields = ('uploaded_at',)