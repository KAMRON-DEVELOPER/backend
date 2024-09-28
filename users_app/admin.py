from .models import CustomUser, Note, Tab, Follow, Profession
from django.contrib import admin
from django.contrib.auth.models import Group


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'auth_type', 'phone_number', 'email', 'location']


class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following']


class TabAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'name')


class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'body', 'category')


class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


admin.site.unregister(Group)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Tab, TabAdmin)
admin.site.register(Profession, ProfessionAdmin)
