from django.contrib import admin
from .models import Room, Post, PostCategory, PostComment, PostLike, Tag, RoomMessage


class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "room_type"]


class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ["room", "user", "text_message"]


class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "content", "author", "category"]


class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ["category_name"]


class PostCommentAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "comment", "image", "parent"]


class PostLikeAdmin(admin.ModelAdmin):
    list_display = ["post", "user"]


class TagAdmin(admin.ModelAdmin):
    list_display = ["tag_name"]


admin.site.register(Room, RoomAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(PostCategory, PostCategoryAdmin)
admin.site.register(PostComment, PostCommentAdmin)
admin.site.register(PostLike, PostLikeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RoomMessage, RoomMessageAdmin)
