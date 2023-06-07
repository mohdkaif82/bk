# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pandas as pd
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from .models import Meeting, MeetingJoinee, MeetingChat,VideoCall
from .permissions import MeetingPermissions
from .serializers import MeetingSerializer, MeetingDetailsSerializer, MeetingJoineeDataSerializer, \
    MeetingJoineeSerializer, MeetingChatSerializer, MeetingChatDataSerializer,VideoCallSerializer
from ..utils import timezone
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import render
from django.http import JsonResponse
import random
import time
from agora_token_builder import RtcTokenBuilder
from .models import RoomMember
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from ..patients.models import Patients

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

# @login_required('')
def lobby(request,id):
    # if request.user.is_authenticated():
    meeting= VideoCall.objects.filter(call_id=id,is_active=True)
    if meeting.exists():
        meeting=meeting.first()
        print("Meeting",meeting)
        print('doctor',meeting.doctors_call.user.email) 
        doctor=False
        if not Patients.objects.filter(user=request.user).exists():
            doctor=True
        return render(request, 'base/lobby.html',{'meeting':meeting,'doctor':doctor})
    else:
        return response.BadRequest('Meeting not found')
    # return response.BadRequest('Please login first')
    

def room(request):
    return render(request, 'base/room.html')

class VideoCallView(ModelViewSet):
    serializer_class = VideoCallSerializer
    queryset = VideoCall.objects.all()
    permission_classes = (MeetingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(VideoCallView, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
def getToken(request):
    appId = "7a9556cdfd984af3805fe3fb809ebf80"
    appCertificate = "2b2e6e0135254a55974113443b39c9b5"
    channelName = request.GET.get('channel')
    duration=request.GET.get('duration')
    uid = random.randint(1, 230)
    expirationTimeInSeconds = int(duration)*60
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)

    return JsonResponse({'token': token, 'uid': uid}, safe=False)


@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )

    return JsonResponse({'name':data['name']}, safe=False)


def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')

    member = RoomMember.objects.get(
        uid=uid,
        room_name=room_name,
    )
    name = member.name
    return JsonResponse({'name':member.name}, safe=False)

@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    return JsonResponse('Member deleted', safe=False)