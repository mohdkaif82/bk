from .models import ArogyamCategory, ArogyamTags, ArogyamVideoFile, ArogyamDisease, \
    ArogyamEvents, ArogyamContactUs, ArogyamPageSEO, ArogyamSlider, ArogyamRating, ArogyamComment,\
        ArogyamSuggestionBox,ArogyamContactUsForm
from django.contrib import admin


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'is_active')


class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(ArogyamSuggestionBox)
class ArogyamSuggestionBoxAdmin(admin.ModelAdmin):
    pass

@admin.register(ArogyamContactUsForm)
class ArogyamContactUsFormAdmin(admin.ModelAdmin):
    pass

@admin.register(ArogyamVideoFile)
class ArogyamVideoFileAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamDisease)
class ArogyamDiseaseAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamEvents)
class ArogyamEventsAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamContactUs)
class ArogyamContactUsAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamPageSEO)
class ArogyamPageSEOAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamSlider)
class ArogyamSliderAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamRating)
class ArogyamRatingAdmin(admin.ModelAdmin):
    pass


@admin.register(ArogyamComment)
class ArogyamCommentAdmin(admin.ModelAdmin):
    pass


admin.site.register(ArogyamCategory, CategoryAdmin)
admin.site.register(ArogyamTags, TagsAdmin)
