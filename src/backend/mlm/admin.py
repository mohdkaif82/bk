from django.contrib import admin
from .models import ProductMargin, RoleComission


# Register your models here.

@admin.register(ProductMargin)
class ProductMarginAdmin(admin.ModelAdmin):
    pass


@admin.register(RoleComission)
class RoleComissionAdmin(admin.ModelAdmin):
    pass
