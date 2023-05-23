from ..base.serializers import ModelSerializer
from .models import AppSlider, AppTestimonial, AppBlog, AppBlogCategory, AppYoutubeCategory, AppYoutube


class AppSliderSerializer(ModelSerializer):
    class Meta:
        model = AppSlider
        fields = '__all__'


class AppTestimonialSerializer(ModelSerializer):
    class Meta:
        model = AppTestimonial
        fields = '__all__'


class AppBlogCategorySerializer(ModelSerializer):
    class Meta:
        model = AppBlogCategory
        fields = '__all__'


class AppBlogSerializer(ModelSerializer):
    class Meta:
        model = AppBlog
        fields = '__all__'


class AppYoutubeCategorySerializer(ModelSerializer):
    class Meta:
        model = AppYoutubeCategory
        fields = '__all__'


class AppYoutubeSerializer(ModelSerializer):
    class Meta:
        model = AppYoutube
        fields = '__all__'
