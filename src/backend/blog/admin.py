from .models import Category, Tags, VideoFile, Disease, Events, ContactUs, PageSEO, Slider, Facility, \
    LandingPageContent, LandingPageVideo, Rating, Comment, BlogImage, ProductContent, TherapyContent,DiseaseList,\
    SymptomList
from django.contrib import admin


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'is_active')


class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    pass

@admin.register(SymptomList)
class SymptomListAdmin(admin.ModelAdmin):
    pass 

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    pass

@admin.register(DiseaseList)
class DiseaseListAdmin(admin.ModelAdmin):
    pass


@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    pass


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    pass


@admin.register(PageSEO)
class PageSEOAdmin(admin.ModelAdmin):
    pass


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    pass


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    pass


@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    pass


@admin.register(LandingPageVideo)
class LandingPageVideoAdmin(admin.ModelAdmin):
    pass


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductContent)
class ProductContentAdmin(admin.ModelAdmin):
    pass


@admin.register(TherapyContent)
class TherapyContentAdmin(admin.ModelAdmin):
    pass


admin.site.register(Category, CategoryAdmin)
admin.site.register(Tags, TagsAdmin)
