import datetime
import random
import string

import pandas as pd
from ..base.serializers import ModelSerializer, serializers
from .models import Meeting, MeetingJoinee, MeetingChat,VideoCall
from ..patients.serializers import PatientsBasicDataSerializer
from ..practice.serializers import PracticeStaffBasicSerializer
from ..patients.models import Patients
from ..utils.email import video_email

class MeetingDetailsSerializer(ModelSerializer):
    patients = PatientsBasicDataSerializer(required=False, many=True)
    doctors = PracticeStaffBasicSerializer(required=False, many=True)
    admins = PracticeStaffBasicSerializer(required=False, many=True)

    class Meta:
        model = Meeting
        fields = '__all__'


class MeetingSerializer(ModelSerializer):
    patients_data = serializers.SerializerMethodField(required=False)
    doctors_data = serializers.SerializerMethodField(required=False)
    admins_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Meeting
        fields = '__all__'

    def validate(self, data):
        if "start" in data and "duration" in data and data["start"] and data["duration"]:
            data["end"] = pd.to_datetime(data["start"]) + datetime.timedelta(minutes=data["duration"])
        return data

    def create(self, validated_data):
        admins = validated_data.pop("admins", [])
        doctors = validated_data.pop("doctors", [])
        patients = validated_data.pop("patients", [])
        validated_data["meeting_id"] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        meeting_obj = Meeting.objects.create(**validated_data)
        meeting_obj.doctors.set(doctors)
        meeting_obj.admins.set(admins)
        meeting_obj.patients.set(patients)
        meeting_obj.save()
        return meeting_obj

    def update(self, instance, validated_data):
        admins = validated_data.pop("admins", [])
        doctors = validated_data.pop("doctors", [])
        patients = validated_data.pop("patients", [])
        validated_data["meeting_id"] = instance.meeting_id
        Meeting.objects.filter(id=instance.id).update(**validated_data)
        meeting_obj = Meeting.objects.get(id=instance.id)
        meeting_obj.patients.set([])
        meeting_obj.admins.set([])
        meeting_obj.doctors.set([])
        meeting_obj.save()
        meeting_obj.doctors.set(doctors)
        meeting_obj.admins.set(admins)
        meeting_obj.patients.set(patients)
        meeting_obj.save()
        return validated_data

    def get_patients_data(self, obj):
        return PatientsBasicDataSerializer(obj.patients.all(), many=True).data

    def get_doctors_data(self, obj):
        return PracticeStaffBasicSerializer(obj.doctors.all(), many=True).data

    def get_admins_data(self, obj):
        return PracticeStaffBasicSerializer(obj.admins.all(), many=True).data


class MeetingJoineeSerializer(ModelSerializer):
    class Meta:
        model = MeetingJoinee
        fields = '__all__'


class MeetingJoineeDataSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)
    staff = PracticeStaffBasicSerializer(required=False)

    class Meta:
        model = MeetingJoinee
        fields = '__all__'


class MeetingChatSerializer(ModelSerializer):
    class Meta:
        model = MeetingChat
        fields = '__all__'


class MeetingChatDataSerializer(ModelSerializer):
    joinee = MeetingJoineeDataSerializer(required=False)

    class Meta:
        model = MeetingChat
        fields = '__all__'
        
        
from ..utils import timezone
class VideoCallSerializer(ModelSerializer):
    # patients_call=serializers.SerializerMethodField(required=False)
    class Meta:
        model = VideoCall
        fields = '__all__'
        
    
    def create(self, validated_data):
        validated_data["call_id"] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        request = self.context.get('request')
        patient=Patients.objects.filter(user=request.user)
        if patient.exists():
            patient=patient.first()
            validated_data["patients_call"]=patient
            validated_data["is_active"]=True
            obj=VideoCall.objects.create(**validated_data)
            video_email(obj)
            print('send')
            return obj
        else:
            raise serializers.ValidationError({"detail": "You are not allowed to make a call"})
    
    def update(self,instance, validated_data):
        instance = VideoCall.objects.get(id=instance.pk)
        request = self.context.get('request')
        if validated_data["status"]=='Scheduled':
            instance.status="Scheduled"
            instance.is_active=True
            instance.cancel_by=''
            instance.cancel_reason=''
            

        elif validated_data["status"]=='Cancelled':
            instance.status="Cancelled"
            instance.cancel_by=request.user.email
            instance.cancel_reason=validated_data["cancel_reason"]
            # instance.is_active=False
            
        elif validated_data["status"]=="ReScheduled":
            instance.status="ReScheduled"
            instance.is_active=True
            instance.cancel_by=''
            instance.cancel_reason=''
            instance.start=validated_data['start']
            
        obj=instance.save()
        video_email(obj=VideoCall.objects.get(id=instance.pk))
        return instance
        
            
    