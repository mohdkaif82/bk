import datetime
import random
import string

from ..accounts.models import User
from ..accounts.serializers import UserSerializer, PatientUserSerializer
from ..base.serializers import ModelSerializer, serializers
from ..constants import CONFIG
from ..inventory.serializers import InventoryItemSerializer
from ..mlm.serializers import AgentRoleSerializer
from ..muster_roll.serializers import HrSettingsSerializer
from .models import Patients, PatientGroups, PatientMedicalHistory, PersonalDoctorsPractice, \
    PatientVitalSigns, PatientClinicNotes, PatientTreatmentPlans, Country, City, State, PatientFile, Source, \
    PatientPrescriptions, PatientMembership, PatientAdvice, PatientInventory, GeneratedPdf, PatientProcedure, \
    PatientNotes, MedicalCertificate, PatientCallNotes, ColdCalling, PatientAllopathicMedicines, PatientRegistration, \
    AdvisorBank
from ..practice.serializers import ProcedureCatalogSerializer, PracticeStaffSerializer, \
    PracticeStaffBasicSerializer, PracticeRefererSerializer, LabTestCatalogSerializer, MembershipSerializer, \
    PracticeBasicSerializer, RegistrationSerializer
from django.conf import settings


class PatientsDetailsSerializer(ModelSerializer):
    class Meta:
        model = Patients
        fields = '__all__'


class ColdCallingSerializer(ModelSerializer):
    class Meta:
        model = ColdCalling
        fields = '__all__'


class CountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class SourceSerializer(ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class StateSerializer(ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'


class CitySerializer(ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class PersonalDoctorsPracticeSerializer(ModelSerializer):
    class Meta:
        model = PersonalDoctorsPractice
        fields = '__all__'


class PatientsPersonalDoctorsPracticeSerializer(ModelSerializer):
    user = UserSerializer(required=True)
    practices = PersonalDoctorsPracticeSerializer(required=False, many=True)
    practices_data = serializers.SerializerMethodField()

    class Meta:
        model = Patients
        fields = ('id', 'user', 'practices', 'practices_data')

    def get_practices_data(self, obj):
        result = []
        for practice in obj.practices.all():
            result.append({
                "practice": practice.practice.id if practice.practice and practice.practice.id else None,
                "practice_name": practice.practice.name if practice.practice and practice.practice.name else None
            })
        return result


class PatientsSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    referal = serializers.CharField(required=False)
    country_extra = serializers.CharField(max_length=1024, required=False)
    state_extra = serializers.CharField(max_length=1024, required=False)
    city_extra = serializers.CharField(max_length=1024, required=False)
    source_extra = serializers.CharField(max_length=1024, required=False)
    check_duplicate = serializers.BooleanField(required=False)
    user = UserSerializer(required=True)
    practices = PersonalDoctorsPracticeSerializer(required=False, many=True)
    medical_history_data = serializers.SerializerMethodField()
    pd_doctor_data = serializers.SerializerMethodField()
    patient_group_data = serializers.SerializerMethodField()
    source_name = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    country_data = serializers.SerializerMethodField()
    state_data = serializers.SerializerMethodField()
    city_data = serializers.SerializerMethodField()
    role_data = serializers.SerializerMethodField()
    practice_data = serializers.SerializerMethodField()
    practices_data = serializers.SerializerMethodField()
    religion_data = serializers.SerializerMethodField()

    class Meta:
        model = Patients
        fields = '__all__'

    def create(self, validated_data):
        country_extra = validated_data.pop('country_extra', None)
        state_extra = validated_data.pop('state_extra', None)
        city_extra = validated_data.pop('city_extra', None)
        source_extra = validated_data.pop('source_extra', None)
        medical_history = validated_data.pop('medical_history', [])
        patient_group = validated_data.pop('patient_group', [])
        practices = validated_data.pop('practices', [])
        user = validated_data.pop('user')
        is_agent = validated_data.get('is_agent', False)
        is_approved = validated_data.get('is_approved', False)
        user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
        referal = validated_data.pop('referal', None)
        check_duplicate = validated_data.pop('check_duplicate', None)
        if check_duplicate and Patients.objects.filter(user__mobile=user['mobile']).exists():
            raise serializers.ValidationError({"detail": "Patient already exists with this mobile number"})
        if not user_data:
            if referal and not User.objects.filter(referer_code=referal).exists():
                raise serializers.ValidationError({"detail": "Invalid Referal Code..!"})
            referer_code = self.generate_refer_code(user['first_name'])
            user_data = User.objects.create(mobile=user['mobile'], first_name=user['first_name'], is_active=True,
                                            referer_code=referer_code)
            user_data.email = user.get('email', None)
            if referal and User.objects.filter(referer_code=referal).exists():
                user_data.referer = User.objects.filter(referer_code=referal).first()
            elif referal:
                referal = CONFIG["config_default_referal"]
                user_data.referer = User.objects.filter(referer_code=referal).first()
            user_data.save()
            user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
        else:
            if not is_agent and Patients.objects.filter(user__id=user_data['id'], is_agent=False,
                                                        is_active=True).exists():
                raise serializers.ValidationError({"detail": "Patient with this mobile no already exists",
                                                   "id": Patients.objects.filter(user__id=user_data['id'],
                                                                                 is_active=True).first().pk})
            elif is_agent and Patients.objects.filter(user__id=user_data['id'], is_agent=True,
                                                      is_active=True).exists():
                raise serializers.ValidationError({"detail": "Advisor with this mobile no already exists",
                                                   "id": Patients.objects.filter(user__id=user_data['id'],
                                                                                 is_active=True).first().pk})
            elif is_agent:
                if referal and User.objects.filter(referer_code=referal).exists():
                    referer = User.objects.filter(referer_code=referal).first()
                    User.objects.filter(mobile=user['mobile']).update(referer=referer, is_active=True)
                elif referal:
                    referal = CONFIG["config_default_referal"]
                    referer = User.objects.filter(referer_code=referal).first()
                    User.objects.filter(mobile=user['mobile']).update(referer=referer, is_active=True)
            User.objects.filter(mobile=user['mobile']).update(is_active=True)
        patient = Patients.objects.filter(user__id=user_data['id']).all().first()
        if "pd_doctor" in validated_data and validated_data["pd_doctor"]:
            validated_data["pd_doctor_added"] = datetime.datetime.now()
        if country_extra:
            validated_data["country"] = Country.objects.create(name=country_extra)
        if source_extra:
            validated_data["source"] = Source.objects.create(name=source_extra)
        if state_extra:
            validated_data["state"] = State.objects.create(name=state_extra, country=validated_data["country"])
        if city_extra:
            validated_data["city"] = City.objects.create(name=city_extra, state=validated_data["state"])
        if is_agent and is_approved:
            validated_data["advisor_joined"] = datetime.datetime.now()
        if patient and user_data:
            validated_data["is_active"] = True
            Patients.objects.filter(id=patient.pk).update(**validated_data)
            patient = Patients.objects.get(id=patient.pk)
            patient.medical_history.set(medical_history)
            patient.patient_group.set(patient_group)
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
        elif not patient and user_data:
            patient = Patients.objects.create(**validated_data)
            if patient.custom_id is None:
                patient.custom_id = "BK" + str(patient.pk)
            patient.user = User.objects.get(id=user_data['id'])
            patient.medical_history.set(medical_history)
            patient.patient_group.set(patient_group)
            pdp = []
            for practice_data in practices:
                pdp.append(PersonalDoctorsPractice.objects.create(**practice_data))
            patient.practices.set(pdp)
            patient.save()
        if not user_data:
            raise serializers.ValidationError("Send user with patient.")
        elif not patient:
            raise serializers.ValidationError("Invalid Patient Data.")
        else:
            return patient

    def get_medical_history_data(self, obj):
        return obj.medical_history.values() if obj.medical_history else []

    def get_patient_group_data(self, obj):
        return obj.patient_group.values() if obj.patient_group else []

    def get_country_data(self, obj):
        return CountrySerializer(obj.country).data if obj.country else None

    def get_state_data(self, obj):
        return StateSerializer(obj.state).data if obj.state else None

    def get_city_data(self, obj):
        return CitySerializer(obj.city).data if obj.city else None

    def get_role_data(self, obj):
        return AgentRoleSerializer(obj.role).data if obj.role else None

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_source_name(self, obj):
        return obj.source.name if obj.source else None

    def get_creator(self, obj):
        return obj.created_by.first_name if obj.created_by else None

    def get_pd_doctor_data(self, obj):
        return PracticeStaffBasicSerializer(obj.pd_doctor).data if obj.pd_doctor else None

    def get_religion_data(self, obj):
        return HrSettingsSerializer(obj.religion).data if obj.religion else None

    def generate_refer_code(self, first_name):
        while True:
            letters = string.ascii_uppercase + string.digits
            name = first_name.replace(".", "").replace(" ", "")[0:4].upper()
            code = ''.join(random.choice(letters) for _ in range(8 - len(name)))
            refer_code = name + code
            if not User.objects.filter(referer_code=refer_code).exists():
                return refer_code

    def get_practices_data(self, obj):
        result = []
        for practice in obj.practices.all():
            result.append({
                "practice": practice.practice.id if practice.practice and practice.practice.id else None,
                "practice_name": practice.practice.name if practice.practice and practice.practice.name else None
            })
        return result


class PatientMembershipSerializer(ModelSerializer):
    class Meta:
        model = PatientMembership
        fields = '__all__'


class PatientRegistrationSerializer(ModelSerializer):
    class Meta:
        model = PatientRegistration
        fields = '__all__'


class PatientMedicalHistorySerializer(ModelSerializer):
    class Meta:
        model = PatientMedicalHistory
        fields = '__all__'


class PatientsBasicDataSerializer(ModelSerializer):
    user = PatientUserSerializer(required=True)

    class Meta:
        model = Patients
        fields = ('id', 'user', 'gender', 'custom_id', 'image')


class PatientAllopathicMedicinesSerializer(ModelSerializer):
    patient_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientAllopathicMedicines
        fields = '__all__'

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None


class ColdCallingDataSerializer(ModelSerializer):
    city = CitySerializer(required=False)
    state = StateSerializer(required=False)
    country = CountrySerializer(required=False)
    medical_history = PatientMedicalHistorySerializer(required=False, many=True)
    created_staff = PracticeStaffBasicSerializer(required=False)
    created_advisor = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = ColdCalling
        fields = '__all__'


class PatientsFollowUpSerializer(ModelSerializer):
    user = PatientUserSerializer(required=True)
    follow_up_staff = PracticeStaffBasicSerializer(required=True)

    class Meta:
        model = Patients
        fields = (
            'id', 'user', 'gender', 'custom_id', 'follow_up_staff', 'follow_up_date', 'medicine_from', 'medicine_till')


class PatientMembershipReportSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)
    medical_membership = MembershipSerializer(required=False)

    class Meta:
        model = PatientMembership
        fields = '__all__'


class PatientRegistrationReportSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)
    registration = MembershipSerializer(required=False)

    class Meta:
        model = PatientRegistration
        fields = '__all__'


class PatientsReferalSerializer(ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Patients
        fields = ('id', 'user', 'gender', 'image', 'is_agent', 'is_approved', 'practice', 'custom_id')


class PatientVitalSignsSerializer(ModelSerializer):
    practice_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientVitalSigns
        fields = '__all__'

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None


class PatientGroupsSerializer(ModelSerializer):
    patient_count = serializers.SerializerMethodField()
    practice_count = serializers.SerializerMethodField()

    class Meta:
        model = PatientGroups
        fields = '__all__'

    def get_patient_count(self, obj):
        return len(Patients.objects.filter(patient_group=obj.id, is_active=True))

    def get_practice_count(self, obj):
        from ..practice.models import Practice
        result = {}
        practices = Practice.objects.filter(is_active=True)
        for practice in practices:
            count = len(Patients.objects.filter(patient_group=obj.id, practices__practice=practice, is_active=True))
            result["practice_" + str(practice.id)] = count
        return result


class PatientsDataSerializer(ModelSerializer):
    refered_by = PracticeRefererSerializer(required=True)
    medical_history = PatientMedicalHistorySerializer(required=False)
    patient_group = PatientGroupsSerializer(required=False)

    class Meta:
        model = Patients
        fields = '__all__'


class PatientMembershipDataSerializer(ModelSerializer):
    medical_membership = MembershipSerializer(required=False)
    practice = PracticeBasicSerializer(required=False)

    class Meta:
        model = PatientMembership
        fields = '__all__'


class PatientRegistrationDataSerializer(ModelSerializer):
    registration = RegistrationSerializer(required=False)
    practice = PracticeBasicSerializer(required=False)

    class Meta:
        model = PatientRegistration
        fields = '__all__'


class PatientClinicNotesSerializer(ModelSerializer):
    follow_up_date = serializers.DateField(required=False)

    class Meta:
        model = PatientClinicNotes
        fields = '__all__'


class PatientClinicNotesDataSerializer(ModelSerializer):
    doctor = PracticeStaffBasicSerializer(required=False)
    follow_up = serializers.SerializerMethodField()
    practice = PracticeBasicSerializer(required=False)
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = PatientClinicNotes
        fields = '__all__'

    def get_follow_up(self, obj):
        return obj.patient.follow_up_date


class PatientTreatmentPlansSerializer(ModelSerializer):
    class Meta:
        model = PatientTreatmentPlans
        fields = '__all__'


class PatientCallNotesSerializer(ModelSerializer):
    class Meta:
        model = PatientCallNotes
        fields = '__all__'


class PatientCallNotesDetailSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer()
    practice_staff = PracticeStaffBasicSerializer()
    practice = PracticeBasicSerializer()

    class Meta:
        model = PatientCallNotes
        fields = '__all__'


class PatientTreatmentPlansDataSerializer(ModelSerializer):
    procedure = ProcedureCatalogSerializer(required=False)
    practice = PracticeBasicSerializer(required=False)

    class Meta:
        model = PatientTreatmentPlans
        fields = '__all__'


class PatientProcedureDataSerializer(ModelSerializer):
    treatment_plans = PatientTreatmentPlansDataSerializer(required=False, many=True)
    doctor = PracticeStaffBasicSerializer(required=False)
    summary_amount = serializers.SerializerMethodField()
    practice = PracticeBasicSerializer(required=False)
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = PatientProcedure
        fields = '__all__'

    def get_summary_amount(self, obj):
        treatment_plans = obj.treatment_plans.all()
        total_amount = 0
        discount = 0
        for treatment_plan in treatment_plans:
            amount = treatment_plan.cost * treatment_plan.quantity
            total_amount += amount
            if treatment_plan.discount_type == "%" and treatment_plan.discount:
                dis = amount * treatment_plan.discount / 100
            elif treatment_plan.discount_type == "INR" and treatment_plan.discount:
                dis = treatment_plan.discount
            else:
                dis = 0
            discount += dis
        grand_total = total_amount - discount
        return {"total_amount": total_amount, "discount": discount, "grand_total": grand_total}


class PatientProcedureSerializer(ModelSerializer):
    treatment_plans = PatientTreatmentPlansSerializer(required=False, many=True)

    class Meta:
        model = PatientProcedure
        fields = '__all__'


class PatientFileSerializer(ModelSerializer):
    practice_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientFile
        fields = '__all__'

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None


class AdvisorBankSerializer(ModelSerializer):
    class Meta:
        model = AdvisorBank
        fields = '__all__'


class AdvisorBankDataSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = AdvisorBank
        fields = '__all__'


class PatientInventorySerializer(ModelSerializer):
    class Meta:
        model = PatientInventory
        fields = '__all__'


class PatientInventoryDataSerializer(ModelSerializer):
    inventory = InventoryItemSerializer(required=False)

    class Meta:
        model = PatientInventory
        fields = '__all__'


class PatientPrescriptionsSerializer(ModelSerializer):
    drugs = PatientInventorySerializer(required=False, many=True)

    class Meta:
        model = PatientPrescriptions
        fields = '__all__'


class PatientAdviceSerializer(ModelSerializer):
    class Meta:
        model = PatientAdvice
        fields = '__all__'


class PatientDrugsSerializer(ModelSerializer):
    class Meta:
        model = PatientInventory
        fields = '__all__'


class PatientPrescriptionsDataSerializer(ModelSerializer):
    practice = PracticeBasicSerializer(required=False)
    drugs = PatientInventoryDataSerializer(required=False, many=True)
    labs = LabTestCatalogSerializer(required=True, many=True)
    doctor = PracticeStaffBasicSerializer(required=False)
    advice_data = PatientAdviceSerializer(required=False, many=True)
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = PatientPrescriptions
        fields = '__all__'


class GeneratedPdfSerializer(ModelSerializer):
    report = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedPdf
        fields = '__all__'

    def get_report(self, obj):
        return settings.MEDIA_URL + obj.report.name if obj.report else None


class PatientNotesSerializer(ModelSerializer):
    class Meta:
        model = PatientNotes
        fields = '__all__'


class PatientNotesDataSerializer(ModelSerializer):
    staff = PracticeStaffSerializer(required=False)
    practice = PracticeBasicSerializer(required=False)

    class Meta:
        model = PatientNotes
        fields = '__all__'


class MedicalCertificateSerializer(ModelSerializer):
    excuse_date_days = serializers.SerializerMethodField(required=False)

    class Meta:
        model = MedicalCertificate
        fields = '__all__'

    def get_excuse_date_days(self, obj):
        days = 0
        if obj.excused_duty and obj.excused_duty_from and obj.excused_duty_to:
            days = (obj.excused_duty_to - obj.excused_duty_from).days
        if obj.excused_duty and (
                obj.excused_duty_from_session == "Morning" and obj.excused_duty_to_session == "Morning") or (
                obj.excused_duty_from_session == "Evening" and obj.excused_duty_to_session == "Evening"):
            days += 0.5
        if obj.excused_duty and (
                obj.excused_duty_from_session == "Morning" and obj.excused_duty_to_session == "Evening"):
            days += 1
        return days
