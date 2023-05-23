from django.contrib import admin
from .models import  PointsToBusinessAdvisor, ProductMarginAdvisor, RoleComissionAdvisor


# Register your models here.

@admin.register(ProductMarginAdvisor)
class ProductMarginAdvisorAdmin(admin.ModelAdmin):
    pass


@admin.register(RoleComissionAdvisor)
class RoleComissionAdvisorAdmin(admin.ModelAdmin):
    pass

@admin.register(PointsToBusinessAdvisor)
class PointsToBusinessAdvisorAdmin(admin.ModelAdmin):
    pass
