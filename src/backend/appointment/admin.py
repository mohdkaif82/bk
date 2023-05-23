from django.contrib import admin
from .models import Appointment


# Register your models here.
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    model = Appointment
