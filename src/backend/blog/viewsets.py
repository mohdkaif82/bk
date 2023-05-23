# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import json

from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from .constants import SUBCATEGORY
from .filters import ConversionFilter, DiseaseListFilter, SymptomListFilter, MedicinesFilter, \
    DynamicDataFilter, CareersApplicationFilter, DiseaseCategoryFilter
from .models import Post, VideoFile, Disease, Events, ContactUs, PageSEO, Slider, Facility, SuggestionBox, \
    LandingPageContent, LandingPageVideo, Comment, Rating, BlogImage, ContactUsForm, ProductContent, TherapyContent, \
    Conversion, DiseaseList, Medicines, SymptomList, ProductSale, DynamicData, CareersApplication, DiseaseCategory
from .permissions import PostPermissions, VideoFilePermissions, DiseasePermissions, EventsPermissions, \
    ContactUsPermissions, PageSEOPermissions, SliderPermissions, FacilityPermissions, LandingPageContentPermissions, \
    LandingPageVideoPermissions, SuggestionBoxPermissions, CommentPermissions, RatingPermissions, BlogImagePermissions, \
    ContactUsFormPermissions, ProductContentPermissions, TherapyContentPermissions, ConversionPermissions, \
    DynamicDataPermissions, CareersApplicationPermissions
from .serializers import PostSerializer, VideoFileSerializer, DiseaseSerializer, EventsSerializer, \
    ContactUsSerializer, SuggestionBoxSerializer, ConversionSerializer, PageSEOSerializer, SliderSerializer, \
    FacilitySerializer, LandingPageContentSerializer, LandingPageVideoSerializer, CommentSerializer, RatingSerializer, \
    BlogImageSerializer, ContactUsFormSerializer, ProductContentSerializer, TherapyContentSerializer, \
    DiseaseListSerializer, MedicinesSerializer, SymptomListSerializer, ProductSaleSerializer, DynamicDataSerializer, \
    CareersApplicationSerializer, DiseaseCategorySerializer, DiseaseListDataSerializer, DiseaseListDetailSerializer
from ..constants import CONST_GLOBAL_PRACTICE, CONST_ORDER_PLACED_SMS, CONST_ORDER_PREFIX
from ..patients.models import Patients
from ..patients.serializers import PatientsSerializer
from ..patients.services import create_update_record
from ..practice.services import dict_to_mail, payment_capture
from ..utils import timezone, email, sms
from ..utils.short_data import get_client_ip
from django.core.files.base import ContentFile
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    permission_classes = (PostPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PostViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=False)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain', None)
        slug = request.query_params.get('slug', None)
        posts = Post.objects.filter(is_active=True)
        if domain:
            posts = posts.filter(domain=domain)
        if slug:
            posts = posts.filter(slug=slug)
        return response.Ok(PostSerializer(posts.order_by('-id'), many=True).data)

    @action(methods=['GET'], detail=True)
    def comments(self, request, *args, **kwargs):
        instance = self.get_object()
        comments = instance.comments.filter(is_active=True)
        return response.Ok(CommentSerializer(comments.order_by('-id'), many=True).data)

    @action(methods=['GET'], detail=True)
    def ratings(self, request, *args, **kwargs):
        instance = self.get_object()
        ratings = instance.ratings.filter(is_active=True)
        return response.Ok(RatingSerializer(ratings.order_by('-id'), many=True).data)


class VideoFileViewSet(ModelViewSet):
    serializer_class = VideoFileSerializer
    queryset = VideoFile.objects.all()
    permission_classes = (VideoFilePermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(VideoFileViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = VideoFile.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class DiseaseViewSet(ModelViewSet):
    serializer_class = DiseaseSerializer
    queryset = Disease.objects.all()
    permission_classes = (DiseasePermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        category = self.request.query_params.get("category", None)
        domain = self.request.query_params.get("domain", None)
        queryset = super(DiseaseViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        if category:
            queryset = queryset.filter(disease__category=category)
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain')
        diseases = Disease.objects.filter(domain=domain, is_active=True)
        page = self.paginate_queryset(diseases)
        if page is not None:
            return self.get_paginated_response(DiseaseSerializer(page, many=True).data)
        return response.Ok(DiseaseSerializer(diseases, many=True).data)


class EventsViewSet(ModelViewSet):
    serializer_class = EventsSerializer
    queryset = Events.objects.all()
    permission_classes = (EventsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(EventsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=False)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain')
        events = Events.objects.filter(domain=domain, is_active=True)
        return response.Ok(EventsSerializer(events.order_by('-id'), many=True).data)


class ContactUsViewSet(ModelViewSet):
    serializer_class = ContactUsSerializer
    queryset = ContactUs.objects.all()
    permission_classes = (ContactUsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ContactUsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('contact_rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('contact_rank') and request.data.get('contact_rank') != instance.rank:
            try:
                landing = ContactUs.objects.get(contact_rank=request.data.get('contact_rank'))
                landing.contact_rank = instance.contact_rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class PageSEOViewSet(ModelViewSet):
    serializer_class = PageSEOSerializer
    queryset = PageSEO.objects.all()
    permission_classes = (PageSEOPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PageSEOViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('created_at')
        return queryset.order_by('-id')


class SliderViewSet(ModelViewSet):
    serializer_class = SliderSerializer
    queryset = Slider.objects.all()
    permission_classes = (SliderPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(SliderViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        queryset = queryset.order_by('rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = Slider.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class FacilityViewSet(ModelViewSet):
    serializer_class = FacilitySerializer
    queryset = Facility.objects.all()
    permission_classes = (FacilityPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(FacilityViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class LandingPageContentViewSet(ModelViewSet):
    serializer_class = LandingPageContentSerializer
    queryset = LandingPageContent.objects.all()
    permission_classes = (LandingPageContentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(LandingPageContentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class LandingPageVideoViewSet(ModelViewSet):
    serializer_class = LandingPageVideoSerializer
    queryset = LandingPageVideo.objects.all()
    permission_classes = (LandingPageVideoPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(LandingPageVideoViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('-rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = LandingPageVideo.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    permission_classes = (CommentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(CommentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class RatingViewSet(ModelViewSet):
    serializer_class = RatingSerializer
    queryset = Rating.objects.all()
    permission_classes = (RatingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(RatingViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['POST', 'GET'], detail=False)
    def create_with_ip(self, request):
        result_dict = {
            "data": None,
            "average": None
        }
        ip = get_client_ip(request)
        if request.method == 'GET':
            blog_id = request.query_params.get('id', None)
            ratinns_average = Rating.objects.filter(rating__isnull=False, is_active=True).aggregate(Avg('rating'))
            if blog_id and ip:
                ratings = Rating.objects.filter(post__id=blog_id, ip_address=ip, is_active=True)
                result_dict.update({"data": RatingSerializer(ratings, many=True).data, "average": ratinns_average})
            else:
                result_dict.update({"average": ratinns_average})
        else:
            data = request.data.copy()
            if Rating.objects.filter(ip_address=ip).exists():
                rating_obj = Rating.objects.filter(ip_address=ip, is_active=True)[0]
                serializer = RatingSerializer(instance=rating_obj, data=data, partial=True)
            else:
                data['ip_address'] = ip
                serializer = RatingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            create_object = serializer.save()
            ratinns_average = Rating.objects.filter(rating__isnull=False, is_active=True).aggregate(Avg('rating'))
            result_dict.update({"data": RatingSerializer(instance=create_object).data, "average": ratinns_average})
        return response.Ok(result_dict)


class BlogImageViewSet(ModelViewSet):
    serializer_class = BlogImageSerializer
    queryset = BlogImage.objects.all()
    permission_classes = (BlogImagePermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(BlogImageViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['POST'], detail=False)
    def create_with_base64(self, request):
        data = request.data.copy()
        format, imgstr = data['image'].split(';base64,')
        ext = format.split('/')[-1]
        data['image'] = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        serializer = BlogImageSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)

    @action(methods=['POST'], detail=False)
    def multiple(self, request):
        data = {"is_active": True}
        result = []
        req_data = json.loads(base64.b64decode(request.data['images']))
        for obj in req_data:
            img_data = obj.get('data', None)
            img_name = obj.get('path', None)
            if img_data and img_name:
                data['image'] = ContentFile(base64.b64decode(img_data), name=img_name.split("/")[-1])
                data['name'] = img_name.split("/")[-1]
                serializer = BlogImageSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                result.append(serializer.data)
        return response.Ok(result)


class ContactUsFormViewSet(ModelViewSet):
    serializer_class = ContactUsFormSerializer
    queryset = ContactUsForm.objects.all()
    permission_classes = (ContactUsFormPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ContactUsFormViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class ProductContentViewSet(ModelViewSet):
    serializer_class = ProductContentSerializer
    queryset = ProductContent.objects.all()
    permission_classes = (ProductContentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        ids = self.request.query_params.get("ids", None)
        queryset = super(ProductContentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        if ids:
            id_list = ids.split(",")
            queryset = queryset.filter(id__in=id_list)
        return queryset.order_by('-id')

    @action(methods=['GET', 'POST'], detail=False)
    def sale(self, request):
        if request.method == "GET":
            start = request.query_params.get("start", None)
            end = request.query_params.get("end", None)
            status = request.query_params.get("payment_status", None)
            queryset = ProductSale.objects.filter(is_active=True)
            if start and end:
                queryset = queryset.filter(created_at__range=[start, end])
            if status:
                queryset = queryset.filter(payment_status=status)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return response.Ok(ProductSaleSerializer(page, many=True).data)
            return response.Ok(ProductSaleSerializer(queryset, many=True).data)
        else:
            data = request.data.copy()
            mobile_no = data.get('mobile_no')
            if Patients.objects.filter(user__mobile=mobile_no, is_active=True).exists():
                data["patient"] = Patients.objects.get(user__mobile=mobile_no, is_active=True).pk
            else:
                patient_data = {
                    "city": data.get("city", None),
                    "state": data.get("state", None),
                    "country": data.get("country", None),
                    "user": {
                        "first_name": data.get("name", None),
                        "mobile": data.get("mobile_no", None),
                        "email": data.get("email", None)
                    }
                }
                data["patient"] = create_update_record(patient_data, PatientsSerializer, Patients).get("id", None)
            return response.Ok(create_update_record(data, ProductSaleSerializer, ProductSale))

    @action(methods=['POST'], detail=False)
    def update_payment(self, request):
        data = request.data.copy()
        sale_id = data.get("id", None)
        try:
            sale_obj = ProductSale.objects.get(id=sale_id)
        except:
            return response.BadRequest({"detail": "Invalid Sale"})
        payment_id = data.get("payment_id", None)
        amount = sale_obj.total_amount if sale_obj.total_amount else 0
        if payment_id and amount:
            payment_response = payment_capture(payment_id, amount)
            if payment_response["error"]:
                return response.BadRequest(payment_response)
            else:
                sale_obj.payment_id = payment_id
                sale_obj.payment_status = "Successful"
                sale_obj.save()
                patient_name = sale_obj.patient.user.first_name if sale_obj.patient else "User"
                patient_id = sale_obj.patient.custom_id if sale_obj.patient else "--"
                sms_text = CONST_ORDER_PLACED_SMS.format(patient_name, patient_id,
                                                         CONST_ORDER_PREFIX + str(sale_obj.id),
                                                         str(round(sale_obj.total_amount)))
                sms.send_sms(sale_obj.mobile_no, sms_text, "ONLINE ORDER")
                sms.send_sms_without_save(sale_obj.mobile_no, sms_text)
                email.order_placed_email(sale_obj)
                return response.Ok(ProductSaleSerializer(sale_obj).data)
        else:
            return response.BadRequest({"detail": "Invalid Sale"})


class TherapyContentViewSet(ModelViewSet):
    serializer_class = TherapyContentSerializer
    queryset = TherapyContent.objects.all()
    permission_classes = (TherapyContentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(TherapyContentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class SuggestionBoxViewSet(ModelViewSet):
    serializer_class = SuggestionBoxSerializer
    queryset = SuggestionBox.objects.all()
    permission_classes = (SuggestionBoxPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(SuggestionBoxViewSet, self).get_queryset()
        start = self.request.query_params.get("start", None)
        end = self.request.query_params.get("end", None)
        status = self.request.query_params.get("status", None)
        mail_to = self.request.query_params.get('mail_to', None)
        queryset = queryset.filter(is_active=True)
        practice_name = CONST_GLOBAL_PRACTICE
        if start and end:
            start_date = timezone.get_day_start(timezone.from_str(start))
            end_date = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        if status:
            status_list = status.split(",")
            queryset = queryset.filter(status__in=status_list)
        result = queryset.order_by('-id')
        if mail_to:
            ready_data = []
            for index, item in enumerate(result):
                ready_data.append({
                    "S. No.": index + 1,
                    "Date": item.created_at.strftime("%d/%m/%Y") if item.created_at else "--",
                    "Name": item.name if item.name else "--",
                    "Email": item.email if item.email else "--",
                    "Mobile No.": item.mobile if item.mobile else "--",
                    "Subject": item.subject if item.subject else "--",
                    "Description": item.description if item.description else "--"
                })
            subject = "Suggestion Report from " + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime(
                "%d/%m/%Y")
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            dict_to_mail(ready_data, "Suggestion_Report_" + start + "_" + end, mail_to, subject, body)
        return result


class ConversionViewSet(ModelViewSet):
    serializer_class = ConversionSerializer
    queryset = Conversion.objects.all()
    permission_classes = (ConversionPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = None

    def get_queryset(self):
        diseases = self.request.query_params.get("diseases", None)
        queryset = super(ConversionViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        if diseases:
            disease_list = diseases.split(",")
            queryset = queryset.filter(diseases__in=disease_list)
        self.filterset_class = ConversionFilter
        queryset = self.filter_queryset(queryset)
        return queryset.order_by('-id')

    @action(methods=['GET', 'POST'], detail=False)
    def disease_list(self, request, *args, **kwargs):
        if request.method == "GET":
            has_detail = request.query_params.get("has_detail", False)
            queryset = DiseaseList.objects.filter(is_active=True)
            if has_detail:
                diseases = Disease.objects.filter(is_active=True).values_list('disease', flat=True)
                queryset = queryset.filter(id__in=diseases)
            self.filterset_class = DiseaseListFilter
            queryset = self.filter_queryset(queryset)
            if has_detail:
                return response.Ok(DiseaseListDetailSerializer(queryset.order_by("name"), many=True).data)
            return response.Ok(DiseaseListDataSerializer(queryset.order_by("name"), many=True).data)
        else:
            return response.Ok(create_update_record(request, DiseaseListSerializer, DiseaseList))

    @action(methods=['GET', 'POST'], detail=False)
    def disease_category(self, request, *args, **kwargs):
        if request.method == "GET":
            queryset = DiseaseCategory.objects.filter(is_active=True)
            self.filterset_class = DiseaseCategoryFilter
            queryset = self.filter_queryset(queryset)
            return response.Ok(DiseaseCategorySerializer(queryset.order_by("category"), many=True).data)
        else:
            return response.Ok(create_update_record(request, DiseaseCategorySerializer, DiseaseCategory))

    @action(methods=['GET', 'POST'], detail=False)
    def symptom_list(self, request, *args, **kwargs):
        if request.method == "GET":
            queryset = SymptomList.objects.filter(is_active=True)
            self.filterset_class = SymptomListFilter
            queryset = self.filter_queryset(queryset)
            return response.Ok(SymptomListSerializer(queryset.order_by("name"), many=True).data)
        else:
            return response.Ok(create_update_record(request, SymptomListSerializer, SymptomList))

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def medicines(self, request, *args, **kwargs):
        if request.method == "GET":
            queryset = Medicines.objects.filter(is_active=True)
            self.filterset_class = MedicinesFilter
            queryset = self.filter_queryset(queryset)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(MedicinesSerializer(page, many=True).data)
            return response.Ok(MedicinesSerializer(queryset.order_by("name"), many=True).data)
        else:
            return response.Ok(create_update_record(request, MedicinesSerializer, Medicines))


class DynamicDataViewSet(ModelViewSet):
    serializer_class = DynamicDataSerializer
    queryset = DynamicData.objects.all()
    permission_classes = (DynamicDataPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = None

    def get_queryset(self):
        order_by = self.request.query_params.get("order_by", None)
        queryset = super(DynamicDataViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = DynamicDataFilter
        queryset = self.filter_queryset(queryset)
        queryset = queryset.order_by(order_by) if order_by else queryset.order_by('-id')
        return queryset

    @action(methods=['GET'], detail=False)
    def subcategory(self, request):
        category = request.query_params.get("category", None)
        if category:
            return response.Ok(SUBCATEGORY[category] if category in SUBCATEGORY else [])
        return response.BadRequest({"detail": "Please use a category"})


class CareersViewSet(ModelViewSet):
    serializer_class = CareersApplicationSerializer
    queryset = CareersApplication.objects.all()
    permission_classes = (CareersApplicationPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = None

    def get_queryset(self):
        order_by = self.request.query_params.get("order_by", None)
        queryset = super(CareersViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = CareersApplicationFilter
        queryset = self.filter_queryset(queryset)
        queryset = queryset.order_by(order_by) if order_by else queryset.order_by('-id')
        return queryset
