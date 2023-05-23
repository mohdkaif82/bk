from ..accounts.models import User, PasswordResetCode
from ..accounts.serializers import RoleSerializer, UserSerializer, PatientUserSerializer
from ..base.serializers import ModelSerializer, serializers
from ..constants import CONST_STAFF
from ..mlm.serializers import ProductMarginSerializer
from ..muster_roll.serializers import HrSettingsBasicSerializer
from .constants import APP_PERMISSIONS
from .models import Practice, PracticeCalenderSettings, MedicineBookingPackage, OtherDiseases, \
    AppointmentCategory, PracticeStaff, VisitingTime, ProcedureCatalog, Taxes, Membership, PaymentModes, PracticeOffers, \
    PracticeReferer, PracticeComplaints, Observations, Diagnoses, Investigations, Treatmentnotes, Filetags, \
    PracticeVitalSign, Communications, EmailCommunications, LabPanel, LabTestCatalog, DrugCatalog, ExpenseType, \
    Expenses, Vendor, ActivityLog, PracticeUserPermissions, DrugType, DrugUnit, PracticePrintSettings, \
    PracticeStaffRelation, PrescriptionTemplate, Advice, DrugCatalogTemplate, RoomTypeSettings, BedBookingPackage, \
    Medication, PushNotifications, Permissions, PermissionGroup, Registration


class MembershipSerializer(ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'


class RegistrationSerializer(ModelSerializer):
    class Meta:
        model = Registration
        fields = '__all__'


class PracticeStaffBasicSerializer(ModelSerializer):
    user = PatientUserSerializer(required=True)
    department_data = serializers.SerializerMethodField(required=False)
    designation_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PracticeStaff
        fields = ('id', 'registration_number', 'calendar_colour', 'user', 'emp_id', 'is_active', 'department_data',
                  'designation_data')

    def get_department_data(self, obj):
        return HrSettingsBasicSerializer(obj.department).data if obj.department else None

    def get_designation_data(self, obj):
        return HrSettingsBasicSerializer(obj.designation).data if obj.designation else None


class PracticeSerializer(ModelSerializer):
    doctor_data = serializers.SerializerMethodField()

    class Meta:
        model = Practice
        fields = (
            'id', 'name', 'tagline', 'specialisation', 'address', 'locality', 'country', 'city', 'state', 'pincode',
            'contact', 'email', 'website', 'gstin', 'logo', 'language', 'is_active', 'hide_cancelled_payment',
            'hide_cancelled_invoice', 'hide_cancelled_return', 'hide_cancelled_proforma', 'payment_prefix',
            'invoice_prefix', 'return_prefix', 'proforma_prefix', 'default_doctor', 'doctor_data', 'reg_city',
            'reg_state', 'reg_country')

    def get_doctor_data(self, obj):
        return PracticeStaffBasicSerializer(obj.default_doctor).data


class PracticeBasicDataSerializer(ModelSerializer):
    class Meta:
        model = Practice
        fields = (
            'id', 'name', 'tagline', 'address', 'locality', 'country', 'language', 'city', 'state', 'pincode',
            'contact', 'email', 'website', 'gstin', 'logo', 'default_doctor', 'reg_city', 'reg_state', 'reg_country')


class PracticeBasicSerializer(ModelSerializer):
    class Meta:
        model = Practice
        fields = (
            'id', 'name', 'email', 'logo', 'contact', 'language', 'default_doctor', 'reg_city', 'reg_state',
            'reg_country')


class PracticeCalenderSettingsSerializer(ModelSerializer):
    class Meta:
        model = PracticeCalenderSettings
        fields = '__all__'


class AppointmentCategorySerializer(ModelSerializer):
    class Meta:
        model = AppointmentCategory
        fields = '__all__'


class PracticeStaffSerializer(ModelSerializer):
    user = PatientUserSerializer(required=True)
    practices = serializers.SerializerMethodField(required=False)
    department_data = serializers.SerializerMethodField(required=False)
    designation_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PracticeStaff
        fields = '__all__'

    def create(self, validated_data):
        user = validated_data.pop("user")
        roles = validated_data.pop('role') if 'role' in validated_data else []
        user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
        if not user_data:
            user_data = User.objects.create(mobile=user['mobile'], email=user['email'], first_name=user['first_name'],
                                            is_active=True)
            if 'referer_code' in user and user['referer_code'] and User.objects.filter(
                    referer_code=user['referer_code']).exists():
                user_data.referer = User.objects.filter(referer_code=validated_data['referer_code'])[0]
            user_data.save()
            user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
            user = User.objects.get(id=user_data['id'])
            password_reset_code = PasswordResetCode.objects.create_reset_code(user)
            password_reset_code.send_password_reset_email()
        elif PracticeStaff.objects.filter(user__id=user_data["id"], is_active=True).exists():
            raise serializers.ValidationError({"detail": "Staff already exists with this mobile no"})
        else:
            User.objects.filter(mobile=user['mobile']).update(is_active=True)
        staff_obj = PracticeStaff.objects.create(**validated_data)
        user = User.objects.get(id=user_data['id'])
        staff_obj.user = user
        staff_obj.role.set(roles)
        staff_obj.save()
        return staff_obj

    def get_practices(self, obj):
        staff_id = obj.pk
        return PracticeStaffRelationDataSerializer(PracticeStaffRelation.objects.filter(staff=staff_id), many=True).data

    def get_department_data(self, obj):
        return HrSettingsBasicSerializer(obj.department).data if obj.department else None

    def get_designation_data(self, obj):
        return HrSettingsBasicSerializer(obj.designation).data if obj.designation else None


class VisitingTimeSerializer(ModelSerializer):
    class Meta:
        model = VisitingTime
        fields = '__all__'


class VisitingTimeDataSerializer(ModelSerializer):
    doctor = PracticeStaffSerializer(required=False)

    class Meta:
        model = VisitingTime
        fields = '__all__'


class DoctorSerializer(ModelSerializer):
    role = RoleSerializer(read_only=True, many=True)
    user = UserSerializer(read_only=True)
    practice = PracticeSerializer(read_only=True)

    class Meta:
        model = PracticeStaff
        fields = ('id', 'practice', 'registration_number', 'calender_colour', 'confirmation_sms', 'schedule_sms',
                  'confirmation_email', 'online_appointment_sms', 'update_timing_online', 'user', 'role', 'is_active')


class DoctorInfoSerializer(ModelSerializer):
    class Meta:
        model = PracticeStaff
        fields = ('id', 'practice', 'registration_number', 'calender_colour', 'confirmation_sms', 'schedule_sms',
                  'confirmation_email', 'online_appointment_sms', 'update_timing_online', 'is_active')


class TaxesSerializer(ModelSerializer):
    class Meta:
        model = Taxes
        fields = '__all__'


class ProcedureCatalogDataSerializer(ModelSerializer):
    taxes = TaxesSerializer(required=False, many=True)
    state_taxes = TaxesSerializer(required=False, many=True)
    margin = ProductMarginSerializer(required=False)
    children = serializers.SerializerMethodField(required=False)

    class Meta:
        model = ProcedureCatalog
        fields = '__all__'

    def get_children(self, obj):
        children = ProcedureCatalog.objects.filter(under=obj.id, is_active=True)
        return ProcedureCatalogDataSerializer(children, many=True).data


class ProcedureCatalogSerializer(ModelSerializer):
    class Meta:
        model = ProcedureCatalog
        fields = '__all__'


class PaymentModesSerializer(ModelSerializer):
    class Meta:
        model = PaymentModes
        fields = '__all__'


class PracticeOffersSerializer(ModelSerializer):
    class Meta:
        model = PracticeOffers
        fields = '__all__'


class PracticeRefererSerializer(ModelSerializer):
    class Meta:
        model = PracticeReferer
        fields = '__all__'


class PracticeComplaintsSerializer(ModelSerializer):
    class Meta:
        model = PracticeComplaints
        fields = '__all__'


class ObservationsSerializer(ModelSerializer):
    class Meta:
        model = Observations
        fields = '__all__'


class CommunicationsSerializer(ModelSerializer):
    class Meta:
        model = Communications
        fields = '__all__'


class EmailCommunicationsSerializer(ModelSerializer):
    class Meta:
        model = EmailCommunications
        fields = '__all__'


class LabPanelSerializer(ModelSerializer):
    class Meta:
        model = LabPanel
        fields = '__all__'


class ExpenseTypeSerializer(ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = '__all__'


class LabTestCatalogSerializer(ModelSerializer):
    class Meta:
        model = LabTestCatalog
        fields = '__all__'


class LabPanelDataSerializer(ModelSerializer):
    tests = LabTestCatalogSerializer(required=False, many=True)

    class Meta:
        model = LabPanel
        fields = '__all__'


class DrugTypeSerializer(ModelSerializer):
    class Meta:
        model = DrugType
        fields = '__all__'


class DrugCatalogSerializer(ModelSerializer):
    class Meta:
        model = DrugCatalog
        fields = '__all__'


class DiagnosesSerializer(ModelSerializer):
    class Meta:
        model = Diagnoses
        fields = '__all__'


class InvestigationsSerializer(ModelSerializer):
    class Meta:
        model = Investigations
        fields = '__all__'


class TreatmentnotesSerializer(ModelSerializer):
    class Meta:
        model = Treatmentnotes
        fields = '__all__'


class FiletagsSerializer(ModelSerializer):
    class Meta:
        model = Filetags
        fields = '__all__'


class MedicationSerializer(ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'


class ExpenseTypeDataSerializer(ModelSerializer):
    practice = PracticeSerializer(required=True)

    class Meta:
        model = ExpenseType
        fields = '__all__'


class PracticeComplaintsDataSerializer(ModelSerializer):
    practice = PracticeSerializer(required=True)

    class Meta:
        model = PracticeComplaints
        fields = '__all__'


class VendorSerializer(ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'


class ExpensesSerializer(ModelSerializer):
    class Meta:
        model = Expenses
        fields = '__all__'


class ExpensesDataSerializer(ModelSerializer):
    expense_type = ExpenseTypeSerializer(required=False)
    vendor = VendorSerializer(required=False)
    payment_mode = PaymentModesSerializer(required=False)

    class Meta:
        model = Expenses
        fields = '__all__'


class PracticeUserPermissionsSerializer(ModelSerializer):
    class Meta:
        model = PracticeUserPermissions
        fields = '__all__'


class PracticeStaffRelationSerializer(ModelSerializer):
    class Meta:
        model = PracticeStaffRelation
        fields = '__all__'


class PracticeStaffRelationDataSerializer(ModelSerializer):
    practice = PracticeBasicDataSerializer(required=False)

    class Meta:
        model = PracticeStaffRelation
        fields = '__all__'


class DrugTypeSerializer(ModelSerializer):
    class Meta:
        model = DrugType
        fields = '__all__'


class DrugUnitSerializer(ModelSerializer):
    class Meta:
        model = DrugUnit
        fields = '__all__'


class PracticePrintSettingsSerializer(ModelSerializer):
    class Meta:
        model = PracticePrintSettings
        fields = '__all__'


class PrescriptionTemplateSerializer(ModelSerializer):
    class Meta:
        model = PrescriptionTemplate
        fields = '__all__'


class AdviceSerializer(ModelSerializer):
    class Meta:
        model = Advice
        fields = '__all__'


class DrugCatalogTemplateSerializer(ModelSerializer):
    class Meta:
        model = DrugCatalogTemplate
        fields = '__all__'


class DrugCatalogTemplateDataSerializer(ModelSerializer):
    from ..inventory.serializers import InventoryItemSerializer
    inventory = InventoryItemSerializer(required=False)

    class Meta:
        model = DrugCatalogTemplate
        fields = '__all__'


class PrescriptionTemplateDataSerializer(ModelSerializer):
    practice = PracticeSerializer(required=False)
    drugs = DrugCatalogTemplateDataSerializer(required=False, many=True)
    labs = LabTestCatalogSerializer(required=False, many=True)
    advice_data = AdviceSerializer(required=False, many=True)

    class Meta:
        model = PrescriptionTemplate
        fields = '__all__'


class RoomTypeSettingsSerializer(ModelSerializer):
    class Meta:
        model = RoomTypeSettings
        fields = '__all__'


class BedBookingPackageSerializer(ModelSerializer):
    class Meta:
        model = BedBookingPackage
        fields = '__all__'


class MedicineBookingPackageSerializer(ModelSerializer):
    children = serializers.SerializerMethodField(required=False)

    class Meta:
        model = MedicineBookingPackage
        fields = '__all__'

    def get_children(self, obj):
        children = MedicineBookingPackage.objects.filter(under=obj.id, is_active=True)
        return MedicineBookingPackageDataSerializer(children, many=True).data


class PracticeVitalSignSerializer(ModelSerializer):
    class Meta:
        model = PracticeVitalSign
        fields = '__all__'


class BedBookingPackageDataSerializer(ModelSerializer):
    taxes = TaxesSerializer(many=True)
    state_taxes = TaxesSerializer(many=True)
    final_normal_price = serializers.SerializerMethodField(required=False)
    final_tatkal_price = serializers.SerializerMethodField(required=False)

    class Meta:
        model = BedBookingPackage
        fields = '__all__'

    def get_final_normal_price(self, obj):
        if obj.normal_price and obj.normal_tax_value:
            return round(obj.normal_price + obj.normal_tax_value)
        elif obj.normal_price:
            return round(obj.normal_price)
        else:
            return 0

    def get_final_tatkal_price(self, obj):
        if obj.tatkal_price and obj.tatkal_tax_value:
            return round(obj.tatkal_price + obj.tatkal_tax_value)
        elif obj.tatkal_price:
            return round(obj.tatkal_price)
        else:
            return 0


class MedicineBookingPackageDataSerializer(ModelSerializer):
    taxes = TaxesSerializer(many=True)
    state_taxes = TaxesSerializer(many=True)
    final_price = serializers.SerializerMethodField(required=False)
    children = serializers.SerializerMethodField(required=False)

    class Meta:
        model = MedicineBookingPackage
        fields = '__all__'

    def get_final_price(self, obj):
        if obj.price and obj.tax_value:
            return round(obj.price + obj.tax_value)
        elif obj.price:
            return round(obj.price)
        else:
            return 0

    def get_children(self, obj):
        children = MedicineBookingPackage.objects.filter(under=obj.id, is_active=True)
        return MedicineBookingPackageSerializer(children, many=True).data


class OtherDiseasesSerializer(ModelSerializer):
    class Meta:
        model = OtherDiseases
        fields = '__all__'


class ActivityLogSerializer(ModelSerializer):
    from ..patients.serializers import PatientsBasicDataSerializer
    patient = PatientsBasicDataSerializer()
    staff = PracticeStaffBasicSerializer()
    practice = PracticeBasicDataSerializer()
    user = PatientUserSerializer()
    record_created_by = PatientUserSerializer()

    class Meta:
        model = ActivityLog
        fields = '__all__'


class PushNotificationSerializer(ModelSerializer):
    has_permission = serializers.SerializerMethodField()
    user = PatientUserSerializer(read_only=True)
    practice = PracticeBasicDataSerializer(read_only=True)

    class Meta:
        model = PushNotifications
        fields = '__all__'

    def get_has_permission(self, obj):
        practice = obj.practice.pk if obj.practice else None
        if not obj.user.is_superuser and (
                obj.application == CONST_STAFF or obj.application is None) and obj.open_screen in APP_PERMISSIONS:
            permissions = APP_PERMISSIONS[obj.open_screen]
            result = True
            for and_perms in permissions["and"]:
                result = result and PracticeUserPermissions.objects.filter(practice=practice, codename=and_perms,
                                                                           is_active=True).exists()
            for or_perms in permissions["or"]:
                result = result or PracticeUserPermissions.objects.filter(practice=practice, codename=or_perms,
                                                                          is_active=True).exists()
            return result
        else:
            return True


class PushNotificationSaveSerializer(ModelSerializer):
    class Meta:
        model = PushNotifications
        fields = '__all__'


class PermissionsSerializer(ModelSerializer):
    class Meta:
        model = Permissions
        fields = '__all__'


class PermissionGroupSerializer(ModelSerializer):
    permissions = PermissionsSerializer(many=True)

    class Meta:
        model = PermissionGroup
        fields = '__all__'

    def create(self, validated_data):
        group_permissions = validated_data.pop('permissions', [])
        new_permission = []
        created_group = PermissionGroup.objects.create(**validated_data)
        for permission_data in group_permissions:
            new_permission.append(Permissions.objects.create(**permission_data))
        created_group.permissions.set(new_permission)
        created_group.save()
        return created_group

    def update(self, instance, validated_data):
        permission_data = validated_data.pop('permissions', [])
        PermissionGroup.objects.filter(id=instance.pk).update(**validated_data)
        instance = PermissionGroup.objects.get(id=instance.pk)
        for permissions in permission_data:
            if not instance.permissions.filter(codename=permissions['codename']).exists():
                try:
                    permission = Permissions.objects.get(codename=permissions['codename'])
                except:
                    permission = Permissions.objects.create(codename=permissions['codename'])
                instance.permissions.add(permission)
        instance.save()
        return instance
