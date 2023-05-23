# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pandas as pd
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from .models import Meeting, MeetingJoinee, MeetingChat
from .permissions import MeetingPermissions
from .serializers import MeetingSerializer, MeetingDetailsSerializer, MeetingJoineeDataSerializer, \
    MeetingJoineeSerializer, MeetingChatSerializer, MeetingChatDataSerializer
from ..utils import timezone
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class MeetingViewSet(ModelViewSet):
    serializer_class = MeetingSerializer
    queryset = Meeting.objects.all()
    permission_classes = (MeetingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(MeetingViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        doctors = self.request.query_params.get('doctors', None)
        patients = self.request.query_params.get('patients', None)
        if start:
            start = timezone.get_day_start(timezone.from_str(start))
            queryset = queryset.filter(end__gte=start)
        if end:
            end = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(start__lte=end)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(doctors__in=doctor_list) | queryset.filter(admins__in=doctor_list)
        if patients:
            patient_list = patients.split(",")
            queryset = queryset.filter(patients__in=patient_list)
        return queryset

    @action(methods=['GET'], detail=False)
    def details(self, request, *args, **kwargs):
        queryset = Meeting.objects.all()
        queryset = queryset.filter(is_active=True)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        doctors = request.query_params.get('doctors', None)
        patients = request.query_params.get('patients', None)
        if start:
            start = pd.to_datetime(start)
            queryset = queryset.filter(end__gte=start)
        if end:
            end = pd.to_datetime(end)
            queryset = queryset.filter(start__lte=end)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(doctors__in=doctor_list) | queryset.filter(admins__in=doctor_list)
        if patients:
            patient_list = patients.split(",")
            queryset = queryset.filter(patients__in=patient_list)
        queryset = queryset.distinct()
        return response.Ok(MeetingDetailsSerializer(queryset, many=True).data)

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def meeting_joinee(self, request, *args, **kwargs):
        if request.method == 'GET':
            queryset = MeetingJoinee.objects.filter(is_active=True)
            meeting = request.query_params.get("meeting", None)
            patient = request.query_params.get("patient", None)
            staff = request.query_params.get("staff", None)
            if meeting:
                queryset = queryset.filter(meeting=meeting)
            if patient:
                queryset = queryset.filter(patient=patient)
            if staff:
                queryset = queryset.filter(staff=staff)
            return response.Ok(MeetingJoineeDataSerializer(queryset.order_by('-modified_at'), many=True).data)
        else:
            data = request.data.copy()
            joinee_id = data.get("id", None)
            meeting = data.get("meeting", None)
            staff = data.get("staff", None)
            patient = data.get("patient", None)
            if joinee_id:
                joinee_obj = MeetingJoinee.objects.get(id=joinee_id)
                serializer = MeetingJoineeSerializer(instance=joinee_obj, data=data, partial=True)
            elif meeting and patient and MeetingJoinee.objects.filter(meeting=meeting, patient=patient, is_active=True):
                joinee_obj = MeetingJoinee.objects.get(meeting=meeting, patient=patient, is_active=True)
                serializer = MeetingJoineeSerializer(instance=joinee_obj, data=data, partial=True)
            elif meeting and staff and MeetingJoinee.objects.filter(meeting=meeting, staff=staff, is_active=True):
                joinee_obj = MeetingJoinee.objects.get(meeting=meeting, staff=staff, is_active=True)
                serializer = MeetingJoineeSerializer(instance=joinee_obj, data=data, partial=True)
            else:
                serializer = MeetingJoineeSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(
                MeetingJoineeSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def meeting_chat(self, request, *args, **kwargs):
        if request.method == 'GET':
            queryset = MeetingChat.objects.filter(is_active=True)
            meeting = request.query_params.get("meeting", None)
            patient = request.query_params.get("patient", None)
            patient_approved = request.query_params.get("patient_approved", None)
            staff = request.query_params.get("staff", None)
            is_public = request.query_params.get("is_public", None)
            if meeting:
                queryset = queryset.filter(joinee__meeting=meeting)
            if patient and patient_approved:
                patient_approved = True if patient_approved == 'true' else False
                queryset = queryset.filter(joinee__patient=patient) | queryset.filter(is_public=patient_approved)
            elif patient:
                queryset = queryset.filter(joinee__patient=patient)
            if staff:
                queryset = queryset.filter(joinee__staff=staff)
            if is_public:
                is_public = True if is_public == "true" else False
                queryset = queryset.filter(is_public=is_public)
            page = self.paginate_queryset(queryset.order_by('-created_at'))
            if page is not None:
                return self.get_paginated_response(MeetingChatDataSerializer(page, many=True).data)
            return response.Ok(MeetingChatDataSerializer(queryset.order_by('-created_at'), many=True).data)
        else:
            data = request.data.copy()
            chat_id = data.pop("id", None)
            if chat_id:
                chat_obj = MeetingChat.objects.get(id=chat_id)
                serializer = MeetingChatSerializer(instance=chat_obj, data=data, partial=True)
            else:
                serializer = MeetingChatSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(
                MeetingChatSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})
