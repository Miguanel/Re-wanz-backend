from django.contrib import admin
from .models import ForumPost, Vote, Comment, CommentVote
from tasks.models import Task


# --- AKCJE MASOWE (Dla postów i komentarzy) ---
@admin.action(description="Oznacz wybrane jako usunięte (Soft Delete)")
def mark_as_deleted(modeladmin, request, queryset):
    queryset.update(is_deleted=True)


@admin.action(description="Przywróć wybrane (Cofnij Soft Delete)")
def restore_items(modeladmin, request, queryset):
    queryset.update(is_deleted=False)


# --- WIDOKI LINIOWE (Wyświetlanie komentarzy wewnątrz posta) ---
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0  # Nie wyświetlaj pustych pól na nowe komentarze
    fields = ('author', 'content', 'is_deleted', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True  # Link do pełnej edycji komentarza


# --- REJESTRACJA MODELI ---

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    # Kolumny widoczne na głównej liście postów
    list_display = ('title', 'author', 'is_resolved', 'is_deleted', 'bounty', 'views', 'created_at')

    # Filtry na prawym pasku bocznym
    list_filter = ('is_resolved', 'is_deleted', 'created_at')

    # Pasek wyszukiwania (szuka po tytule, treści i nazwie autora)
    search_fields = ('title', 'content', 'author__username')

    # Podpięcie akcji masowych
    actions = [mark_as_deleted, restore_items]

    # Zagnieżdżenie komentarzy w widoku edycji posta
    inlines = [CommentInline]

    # Zabezpieczenie pól, których admin nie powinien ręcznie nadpisywać
    readonly_fields = ('views', 'upvotes', 'created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'short_content', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    actions = [mark_as_deleted, restore_items]
    readonly_fields = ('created_at', 'updated_at')

    # Metoda skracająca treść komentarza na liście (żeby nie rozpychać tabeli)
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Treść'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'assignee', 'status', 'bounty')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'creator__username', 'assignee__username')



@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'value')
    list_filter = ('value',)
    search_fields = ('user__username', 'post__title')


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'value')
    list_filter = ('value',)
    search_fields = ('user__username', 'comment__content')