import datetime
import random
import string

import pandas as pd
from ..base.serializers import ModelSerializer, serializers
from .models import Meeting, MeetingJoinee, MeetingChat
from ..patients.serializers import PatientsBasicDataSerializer
from ..practice.serializers import PracticeStaffBasicSerializer


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

