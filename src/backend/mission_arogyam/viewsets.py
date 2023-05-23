# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..constants import CONST_GLOBAL_PRACTICE
from .models import ArogyamPost, ArogyamVideoFile, ArogyamDisease, ArogyamEvents, \
    ArogyamContactUs, ArogyamPageSEO, ArogyamSlider, ArogyamSuggestionBox, \
    ArogyamComment, ArogyamRating, ArogyamContactUsForm
from .permissions import PostPermissions, VideoFilePermissions, DiseasePermissions, \
    EventsPermissions, ContactUsPermissions, PageSEOPermissions, SliderPermissions, SuggestionBoxPermissions, \
    CommentPermissions, RatingPermissions, ContactUsFormPermissions
from .serializers import PostSerializer, VideoFileSerializer, DiseaseSerializer, \
    EventsSerializer, ContactUsSerializer, SuggestionBoxSerializer, PageSEOSerializer, \
    SliderSerializer, CommentSerializer, RatingSerializer, ContactUsFormSerializer
from ..practice.services import dict_to_mail
from ..utils import timezone
from ..utils.short_data import get_client_ip
from django.db.models import Avg
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class ArogyamPostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = ArogyamPost.objects.all()
    permission_classes = (PostPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamPostViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=False)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain', None)
        slug = request.query_params.get('slug', None)
        posts = ArogyamPost.objects.filter(is_active=True)
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


class ArogyamVideoFileViewSet(ModelViewSet):
    serializer_class = VideoFileSerializer
    queryset = ArogyamVideoFile.objects.all()
    permission_classes = (VideoFilePermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamVideoFileViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = ArogyamVideoFile.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class ArogyamDiseaseViewSet(ModelViewSet):
    serializer_class = DiseaseSerializer
    queryset = ArogyamDisease.objects.all()
    permission_classes = (DiseasePermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamDiseaseViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain')
        diseases = ArogyamDisease.objects.filter(domain=domain, is_active=True)
        page = self.paginate_queryset(diseases)
        if page is not None:
            return self.get_paginated_response(DiseaseSerializer(page, many=True).data)
        return response.Ok(DiseaseSerializer(diseases, many=True).data)


class ArogyamEventsViewSet(ModelViewSet):
    serializer_class = EventsSerializer
    queryset = ArogyamEvents.objects.all()
    permission_classes = (EventsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamEventsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=False)
    def slug(self, request, *args, **kwargs):
        domain = request.query_params.get('domain')
        events = ArogyamEvents.objects.filter(domain=domain, is_active=True)
        return response.Ok(EventsSerializer(events.order_by('-id'), many=True).data)


class ArogyamContactUsViewSet(ModelViewSet):
    serializer_class = ContactUsSerializer
    queryset = ArogyamContactUs.objects.all()
    permission_classes = (ContactUsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamContactUsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('contact_rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('contact_rank') and request.data.get('contact_rank') != instance.rank:
            try:
                landing = ArogyamContactUs.objects.get(contact_rank=request.data.get('contact_rank'))
                landing.contact_rank = instance.contact_rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class ArogyamPageSEOViewSet(ModelViewSet):
    serializer_class = PageSEOSerializer
    queryset = ArogyamPageSEO.objects.all()
    permission_classes = (PageSEOPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamPageSEOViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True).order_by('created_at')
        return queryset.order_by('-id')


class ArogyamSliderViewSet(ModelViewSet):
    serializer_class = SliderSerializer
    queryset = ArogyamSlider.objects.all()
    permission_classes = (SliderPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ArogyamSliderViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        queryset = queryset.order_by('rank')
        return queryset.order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.data.get('rank') and request.data.get('rank') != instance.rank:
            try:
                landing = ArogyamSlider.objects.get(rank=request.data.get('rank'))
                landing.rank = instance.rank
                landing.save()
            except Exception as e:
                print(e)

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Ok(serializer.data)


class ArogyamCommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    queryset = ArogyamComment.objects.all()
    permission_classes = (CommentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamCommentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')


class ArogyamRatingViewSet(ModelViewSet):
    serializer_class = RatingSerializer
    queryset = ArogyamRating.objects.all()
    permission_classes = (RatingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ArogyamRatingViewSet, self).get_queryset()
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
            ratinns_average = ArogyamRating.objects.filter(rating__isnull=False, is_active=True).aggregate(
                Avg('rating'))
            if blog_id and ip:
                ratings = ArogyamRating.objects.filter(post__id=blog_id, ip_address=ip, is_active=True)
                result_dict.update({"data": RatingSerializer(ratings, many=True).data, "average": ratinns_average})
            else:
                result_dict.update({"average": ratinns_average})
        else:
            data = request.data.copy()
            if ArogyamRating.objects.filter(ip_address=ip).exists():
                rating_obj = ArogyamRating.objects.filter(ip_address=ip, is_active=True)[0]
                serializer = RatingSerializer(instance=rating_obj, data=data, partial=True)
            else:
                data['ip_address'] = ip
                serializer = RatingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            create_object = serializer.save()
            ratinns_average = ArogyamRating.objects.filter(rating__isnull=False, is_active=True).aggregate(
                Avg('rating'))
            result_dict.update({"data": RatingSerializer(instance=create_object).data, "average": ratinns_average})
        return response.Ok(result_dict)


class ArogyamContactUsFormViewSet(ModelViewSet):
    serializer_class = ContactUsFormSerializer
    queryset = ArogyamContactUsForm.objects.filter(id=1)
    permission_classes = (ContactUsFormPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamContactUsFormViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset.order_by('-id')
        


class ArogyamSuggestionBoxViewSet(ModelViewSet):
    serializer_class = SuggestionBoxSerializer
    queryset = ArogyamSuggestionBox.objects.all()
    permission_classes = (SuggestionBoxPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ArogyamSuggestionBoxViewSet, self).get_queryset()
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
