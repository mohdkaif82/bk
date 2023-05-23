from ..base.serializers import ModelSerializer, serializers
from .models import Post, VideoFile, Disease, Events, ContactUs, PageSEO, Slider, Facility, SuggestionBox, \
    LandingPageContent, LandingPageVideo, Comment, Rating, BlogImage, ContactUsForm, ProductContent, TherapyContent, \
    Conversion, DiseaseList, Medicines, SymptomList, ProductSale, ProductDetail, DynamicData, CareersApplication, \
    DiseaseCategory
from ..patients.serializers import StateSerializer, CitySerializer, CountrySerializer
from ..utils.email import send


class PostSerializer(ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class VideoFileSerializer(ModelSerializer):
    class Meta:
        model = VideoFile
        fields = '__all__'


class DiseaseSerializer(ModelSerializer):
    disease_detail = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = '__all__'

    def get_disease_detail(self, obj):
        return DiseaseListDataSerializer(obj.disease).data if obj.disease else None


class EventsSerializer(ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'


class ContactUsSerializer(ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'


class PageSEOSerializer(ModelSerializer):
    class Meta:
        model = PageSEO
        fields = '__all__'


class SliderSerializer(ModelSerializer):
    class Meta:
        model = Slider
        fields = '__all__'


class FacilitySerializer(ModelSerializer):
    class Meta:
        model = Facility
        fields = '__all__'


class LandingPageContentSerializer(ModelSerializer):
    class Meta:
        model = LandingPageContent
        fields = '__all__'


class LandingPageVideoSerializer(ModelSerializer):
    class Meta:
        model = LandingPageVideo
        fields = '__all__'


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'


class BlogImageSerializer(ModelSerializer):
    class Meta:
        model = BlogImage
        fields = ('id', 'image_path', 'name', 'image', 'is_active')

    def create(self, validated_data):
        validated_data['is_active'] = True
        blog_image = BlogImage.objects.create(**validated_data)
        return blog_image


class ContactUsFormSerializer(ModelSerializer):
    class Meta:
        model = ContactUsForm
        fields = '__all__'

    def create(self, validated_data):
        """
         We will create the userprofile object here. If secondary address present then only create
         secondary_address instance and assign it to userprofile object.
        """

        contact_obj = ContactUsForm.objects.create(**validated_data)
        if contact_obj.email:
            subject = "Contact Us Email"
            text_body = str(contact_obj.mobile) + " . " + str(contact_obj.name) + '. Description ' + str(
                contact_obj.description)
            send(contact_obj.email, contact_obj.subject, '', text_body=text_body)
        return contact_obj


class ProductDetailSerializer(ModelSerializer):
    class Meta:
        model = ProductDetail
        fields = '__all__'


class ProductContentSerializer(ModelSerializer):
    class Meta:
        model = ProductContent
        fields = '__all__'


class DiseaseCategorySerializer(ModelSerializer):
    class Meta:
        model = DiseaseCategory
        fields = '__all__'


class ProductSaleSerializer(ModelSerializer):
    products = ProductDetailSerializer(many=True)

    class Meta:
        model = ProductSale
        fields = '__all__'

    def create(self, validated_data):
        products = validated_data.pop("products")
        product_list, products_final = [], []
        for product in products:
            product["product"] = product["product"].pk
            product_list.append(self.check_valid(ProductDetailSerializer, product, ProductDetail))
        obj = ProductSale.objects.create(**validated_data)
        for product in product_list:
            products_final.append(product.save())
        obj.products.set(products_final)
        obj.save()
        return obj

    def check_valid(self, serializer, data, model=None):
        id = data.pop("id", None)
        if id:
            obj = model.objects.get(id=id)
            var_serializer = serializer(instance=obj, data=data)
        else:
            var_serializer = serializer(data=data)
        var_serializer.is_valid(raise_exception=True)
        return var_serializer


class TherapyContentSerializer(ModelSerializer):
    class Meta:
        model = TherapyContent
        fields = '__all__'


class SuggestionBoxSerializer(ModelSerializer):
    class Meta:
        model = SuggestionBox
        fields = '__all__'


class DiseaseListSerializer(ModelSerializer):
    class Meta:
        model = DiseaseList
        fields = '__all__'


class SymptomListSerializer(ModelSerializer):
    class Meta:
        model = SymptomList
        fields = '__all__'


class DiseaseListDataSerializer(ModelSerializer):
    symptoms = SymptomListSerializer(many=True, required=False)
    category = DiseaseCategorySerializer(required=False)

    class Meta:
        model = DiseaseList
        fields = '__all__'


class DiseaseListDetailSerializer(ModelSerializer):
    symptoms = SymptomListSerializer(many=True, required=False)
    category = DiseaseCategorySerializer(required=False)
    details = serializers.SerializerMethodField(required=False)

    class Meta:
        model = DiseaseList
        fields = '__all__'

    def get_details(self, obj):
        diseases = Disease.objects.filter(disease=obj.id, is_active=True).values_list('domain', flat=True)
        return diseases


class DynamicDataSerializer(ModelSerializer):
    class Meta:
        model = DynamicData
        fields = '__all__'


class CareersApplicationSerializer(ModelSerializer):
    city_data = serializers.SerializerMethodField()
    country_data = serializers.SerializerMethodField()
    state_data = serializers.SerializerMethodField()
    job_data = serializers.SerializerMethodField()

    class Meta:
        model = CareersApplication
        fields = '__all__'

    def validate(self, data):
        if 'job' in data and data['job']:
            applications = CareersApplication.objects.filter(job=data['job'])
            if data['mobile1']:
                applications = applications.filter(mobile1=data['mobile1']) | applications.filter(
                    mobile2=data['mobile1'])
            if 'mobile2' in data and data['mobile2']:
                applications = applications.filter(mobile1=data['mobile2']) | applications.filter(
                    mobile2=data['mobile2'])
            if applications.count() > 0:
                raise serializers.ValidationError({"detail": "You have already applied for this Job Posting"})
        return data

    def get_city_data(self, obj):
        return CitySerializer(obj.city).data if obj.city else None

    def get_state_data(self, obj):
        return StateSerializer(obj.state).data if obj.state else None

    def get_job_data(self, obj):
        return DynamicDataSerializer(obj.job).data if obj.job else None

    def get_country_data(self, obj):
        return CountrySerializer(obj.country).data if obj.country else None


class MedicinesSerializer(ModelSerializer):
    class Meta:
        model = Medicines
        fields = '__all__'


class ConversionSerializer(ModelSerializer):
    diseases_data = serializers.SerializerMethodField()
    allopath_data = serializers.SerializerMethodField()
    ayurveda_data = serializers.SerializerMethodField()

    class Meta:
        model = Conversion
        fields = '__all__'

    def get_diseases_data(self, obj):
        return DiseaseListSerializer(obj.diseases.all(), many=True).data

    def get_allopath_data(self, obj):
        return MedicinesSerializer(obj.allopath.all(), many=True).data

    def get_ayurveda_data(self, obj):
        return MedicinesSerializer(obj.ayurveda.all(), many=True).data
