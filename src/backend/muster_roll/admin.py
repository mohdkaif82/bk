from .models import HrSettings,TaskTemplates,UserTasks,ManagerRating,TargetHeads,\
    UserTarget,MonthlyTarget
from django.contrib import admin


@admin.register(HrSettings)
class HrSettingsAdmin(admin.ModelAdmin):
    pass

@admin.register(TaskTemplates)
class TaskTemplatesAdmin(admin.ModelAdmin):
    pass

@admin.register(UserTasks)
class UserTasksAdmin(admin.ModelAdmin):
    pass

@admin.register(MonthlyTarget)
class MonthlyTargetAdmin(admin.ModelAdmin):
    pass

@admin.register(ManagerRating)
class ManagerRatingAdmin(admin.ModelAdmin):
    pass

@admin.register(TargetHeads)
class TargetHeadsAdmin(admin.ModelAdmin):
    pass

@admin.register(UserTarget)
class UserTargetAdmin(admin.ModelAdmin):
    pass