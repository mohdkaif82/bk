from ..base import response
from ..base.api.viewsets import ModelViewSet
from .models import AppSlider, AppTestimonial, AppBlog, AppBlogCategory, AppYoutubeCategory, AppYoutube
from .permissions import AppSliderPermissions, AppTestimonialPermissions, AppBlogPermissions, \
    AppBlogCategoryPermissions, AppYoutubePermissions, AppYoutubeCategoryPermissions
from .serializers import AppSliderSerializer, AppTestimonialSerializer, AppBlogSerializer, AppBlogCategorySerializer, \
    AppYoutubeSerializer, AppYoutubeCategorySerializer
from rest_framework.parsers import MultiPartParser, JSONParser


class AppSliderViewSet(ModelViewSet):
    serializer_class = AppSliderSerializer
    queryset = AppSlider.objects.all()
    permission_classes = (AppSliderPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppSliderViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        queryset = queryset.order_by('rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = AppSlider.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class AppTestimonialViewSet(ModelViewSet):
    serializer_class = AppTestimonialSerializer
    queryset = AppTestimonial.objects.all()
    permission_classes = (AppTestimonialPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppTestimonialViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class AppBlogViewSet(ModelViewSet):
    serializer_class = AppBlogSerializer
    queryset = AppBlog.objects.all()
    permission_classes = (AppBlogPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppBlogViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class AppBlogCategoryViewSet(ModelViewSet):
    serializer_class = AppBlogCategorySerializer
    queryset = AppBlogCategory.objects.all()
    permission_classes = (AppBlogCategoryPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppBlogCategoryViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class AppYoutubeViewSet(ModelViewSet):
    serializer_class = AppYoutubeSerializer
    queryset = AppYoutube.objects.all()
    permission_classes = (AppYoutubePermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppYoutubeViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class AppYoutubeCategoryViewSet(ModelViewSet):
    serializer_class = AppYoutubeCategorySerializer
    queryset = AppYoutubeCategory.objects.all()
    permission_classes = (AppYoutubeCategoryPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(AppYoutubeCategoryViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')
