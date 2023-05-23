from .models import Meeting, MeetingChat, MeetingJoinee
from django.contrib import admin


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    pass


@admin.register(MeetingJoinee)
class MeetingJoinee(admin.ModelAdmin):
    pass


@admin.register(MeetingChat)
class MeetingChat(admin.ModelAdmin):
    pass
