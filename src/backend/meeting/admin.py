from .models import Meeting, MeetingChat, MeetingJoinee,RoomMember,VideoCall
from django.contrib import admin


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    pass


@admin.register(MeetingJoinee)
class MeetingJoinee(admin.ModelAdmin):
    pass


@admin.register(VideoCall)
class VideoCall(admin.ModelAdmin):
    pass


@admin.register(RoomMember)
class RoomMember(admin.ModelAdmin):
    pass

@admin.register(MeetingChat)
class MeetingChat(admin.ModelAdmin):
    pass
