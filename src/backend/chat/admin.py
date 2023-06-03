from django.contrib import admin
from .models import Room,ActiveUser,TextMessage


admin.site.register(Room)
admin.site.register(ActiveUser)
admin.site.register(TextMessage)
# Register your models here.
