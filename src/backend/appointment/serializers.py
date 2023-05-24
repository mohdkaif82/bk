from datetime import timedelta

import pandas as pd
from ..accounts.models import User
from .models import Appointment, BlockCalendar
from ..base.serializers import ModelSerializer, serializers
from ..patients.models import PatientMedicalHistory, PatientGroups, PatientProcedure, PersonalDoctorsPractice
from ..patients.serializers import PatientProcedureSerializer, PatientProcedureDataSerializer, \
    PatientsBasicDataSerializer
from ..patients.services import update_patient_procedure
from ..practice.serializers import PracticeStaffSerializer, AppointmentCategorySerializer, \
    PracticeBasicSerializer, PracticeStaffBasicSerializer, PracticeBasicDataSerializer
from ..utils.email import appointment_email
from ..utils.sms import prepare_appointment_sms
from ..practice.models import Practice


class AppointmentSerializer(ModelSerializer):
    from ..patients.serializers import PatientsSerializer, PatientTreatmentPlansSerializer
    # patient = PatientsSerializer(required=False)
    patient=serializers.CharField(max_length=244)
    treatment_plans = PatientTreatmentPlansSerializer(required=False, many=True)
    doctor_data = serializers.SerializerMethodField(required=False)
    creator = serializers.SerializerMethodField(required=False)
    category_data = serializers.SerializerMethodField(required=False)
    practice_data = serializers.SerializerMethodField(required=False)
    procedure_data = serializers.SerializerMethodField(required=False)
    schedule_at = serializers.DateTimeField(
        error_messages={
            'required': 'Please enter a valid Schedule Date.',
            'blank': 'Please enter a valid Schedule Date.',
            'null': 'Please enter a valid Schedule Date.'
        },
    )

    class Meta:
        model = Appointment
        fields = '__all__'

    def create(self, validated_data):
        from ..patients.models import Patients
        patient_data = validated_data.pop('patient')
        print('patient',patient_data)
        treatment_plans = validated_data.pop('treatment_plans', [])
        if patient_data:
            try:
                print('run')
                patient=Patients.objects.get(id=patient_data)
                print('patient')
                print('run2',patient.practice.id)
                # patient = Patients.objects.filter(id=patient_data).values('id').first()
            except:
                raise serializers.ValidationError("No such patient exists")
        else:
            medical_history = patient_data.pop('medical_history') if 'medical_history' in patient_data else []
            patient_group = patient_data.pop('patient_group') if 'patient_group' in patient_data else []
            practices = patient_data.pop('practices') if 'practices' in patient_data else []
            user = patient_data.pop('user')
            user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
            if not user_data:
                user_data = User.objects.create(mobile=user['mobile'], email=user['email'],
                                                first_name=user['first_name'], is_active=True)
                if 'referer_code' in user and user['referer_code'] and User.objects.filter(
                        referer_code=user['referer_code']).exists():
                    user_data.referer = User.objects.filter(referer_code=validated_data['referer_code'])[0]
                user_data.save()
                user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
            patient = Patients.objects.filter(user__id=user_data['id']).values('id').first()
            if not patient:
                patient = Patients.objects.create(**patient_data)
                if patient.custom_id is None:
                    patient.custom_id = "BK" + str(patient.pk)
                patient.user = User.objects.get(id=user_data['id'])
                patient.medical_history.set(PatientMedicalHistory.objects.filter(id__in=medical_history))
                patient.patient_group.set(PatientGroups.objects.filter(id__in=patient_group))
                pdp = []
                new_practices = []
                for i in range(len(practices)):
                    for j in range(i + 1, len(practices)):
                        if practices[i]["practice"] == practices[j]["practice"]:
                            break
                    else:
                        new_practices.append(practices[i])
                for practice_data in new_practices:
                    pdp.append(PersonalDoctorsPractice.objects.create(**practice_data))
                patient.practices.set(pdp)
                patient.save()
                patient = Patients.objects.filter(user__id=user_data['id']).values('id').first()
        if "schedule_at" in validated_data and validated_data["schedule_at"] and "slot" in validated_data and \
                validated_data["slot"]:
            validated_data["schedule_till"] = pd.to_datetime(validated_data["schedule_at"]) + timedelta(
                minutes=validated_data["slot"])
        try:
            print('id',patient)
            appointment = Appointment.objects.create(**validated_data, patient=Patients.objects.get(id=patient['id']))
            print('run3')
        except:
            print('run4')
            appointment = Appointment.objects.create(**validated_data, patient=Patients.objects.get(id=patient.id),practice\
                =Practice.objects.get(id=patient.practice.id))
            print('run5')
        if len(treatment_plans):
            for treatment_plan in treatment_plans:
                treatment_plan["procedure"] = treatment_plan["procedure"].pk if treatment_plan["procedure"] else None

            class x:
                data = {}

            x.data = {
                'practice': validated_data.get("practice", None).pk if validated_data.get("practice", None) else None,
                'patient': patient['id'],
                'doctor': validated_data.get("doctor", None).pk if validated_data.get("doctor", None) else None,
                'is_active': True,
                'treatment_plans': treatment_plans,
                'date': validated_data.get("schedule_at").date()
            }
            update_response = update_patient_procedure(x, PatientProcedureSerializer,
                                                       Patients.objects.get(id=patient['id']), PatientProcedure)
            appointment.procedure = PatientProcedure.objects.get(id=update_response["id"])
        appointment.save()
        prepare_appointment_sms(appointment, "CREATE")
        appointment_email(appointment, "CREATE")
        return appointment

    def get_category_data(self, obj):
        return AppointmentCategorySerializer(obj.category).data if obj.category else None

    def get_doctor_data(self, obj):
        return PracticeStaffSerializer(obj.doctor).data if obj.doctor else None

    def get_practice_data(self, obj):
        return PracticeBasicDataSerializer(obj.practice).data if obj.practice else None

    def get_procedure_data(self, obj):
        return PatientProcedureDataSerializer(obj.procedure).data if obj.procedure else None

    def get_creator(self, obj):
        return obj.created_by.first_name if obj.created_by else None


class BlockCalendarSerializer(ModelSerializer):
    class Meta:
        model = BlockCalendar
        fields = '__all__'


class AppointmentDataSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=True)
    creator = serializers.SerializerMethodField(required=False)
    doctor_data = serializers.SerializerMethodField(required=False)
    category_data = serializers.SerializerMethodField(required=False)
    practice_data = serializers.SerializerMethodField(required=False)
    procedure_data = serializers.SerializerMethodField(required=False)
    first_appointment = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Appointment
        fields = '__all__'

    def get_doctor_data(self, obj):
        return PracticeStaffBasicSerializer(obj.doctor).data if obj.doctor else None

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_procedure_data(self, obj):
        return PatientProcedureDataSerializer(obj.procedure).data if obj.procedure else None

    def get_category_data(self, obj):
        return AppointmentCategorySerializer(obj.category).data if obj.category else None

    def get_first_appointment(self, obj):
        count = Appointment.objects.exclude(status='Scheduled').filter(patient=obj.patient, id__lt=obj.id,
                                                                       is_active=True).count()
        return True if count == 0 else False

    def get_creator(self, obj):
        return obj.created_by.first_name if obj.created_by else None
