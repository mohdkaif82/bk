from .models import User, Role, SMS_Records, PatientLogin, StaffLogin, TaskLogin
from ..base.serializers import ModelSerializer
from ..constants import CONFIG
from ..patients.models import Patients
from django.contrib.auth.models import Group, Permission
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class PermissionSerializer(ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(ModelSerializer):
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')


class UserSerializer(ModelSerializer):
    """
    User Serializer
    """
    mobile = serializers.CharField(max_length=20)
    referer_data = serializers.SerializerMethodField(required=False)
    staff = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'mobile', 'last_name', 'is_staff', 'is_active', 'referer_code', 'referer',
            'is_superuser', 'referer_data', 'staff'
        )
        extra_kwargs = {'password': {'write_only': True}, 'referer_code': {'read_only': True},
                        'last_login': {'read_only': True}, 'is_superuser': {'read_only': True}}

    def get_referer_data(self, obj):
        referer = PatientUserSerializer(obj.referer).data if obj.referer else None
        patient = Patients.objects.filter(user=obj.referer).first()
        patient_id = patient.pk if patient else None
        custom_id = patient.custom_id if patient else None
        return {'referer': referer, 'patient': patient_id, 'custom_id': custom_id}

    def get_staff(self, obj):
        from ..practice.models import PracticeStaff
        from ..practice.serializers import PracticeStaffSerializer
        staff = PracticeStaff.objects.filter(user=obj.pk, is_active=True, user__is_active=True).first()
        return PracticeStaffSerializer(staff).data if staff else None


class PatientUserSerializer(ModelSerializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'mobile', 'first_name', 'referer_code', 'is_active', 'last_login', 'is_superuser'
        )
        extra_kwargs = {'password': {'write_only': True}, 'referer_code': {'read_only': True},
                        'last_login': {'read_only': True}, 'is_superuser': {'read_only': True}}


class TaskUserSerializer(ModelSerializer):
    details = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'is_active', 'details')

    def get_details(self, obj):
        from ..practice.models import PracticeStaff
        from ..muster_roll.models import HrSettings
        emp_id, dept, desg, dept_id, desg_id = None, None, None, None, None
        staff_obj = PracticeStaff.objects.filter(user=obj.id, is_active=True).first()
        advisor_obj = Patients.objects.filter(user=obj.id, is_active=True).first()
        if staff_obj:
            emp_id = staff_obj.emp_id
            dept = staff_obj.department.value if staff_obj.department else None
            desg = staff_obj.designation.value if staff_obj.designation else None
            dept_id = staff_obj.department.pk if staff_obj.department else None
            desg_id = staff_obj.designation.pk if staff_obj.designation else None
        elif advisor_obj:
            emp_id = advisor_obj.custom_id
            dept_obj = HrSettings.objects.filter(id=CONFIG["config_advisor_department"]).first()
            desg_obj = HrSettings.objects.filter(id=CONFIG["config_advisor_designation"]).first()
            dept = dept_obj.value if dept_obj else None
            desg = desg_obj.value if desg_obj else None
            dept_id = CONFIG["config_advisor_department"]
            desg_id = CONFIG["config_advisor_designation"]
        return {"emp_id": emp_id, "designation": desg, "department": dept, "department_id": dept_id,
                "designation_id": desg_id}


class LoginSerializer(serializers.Serializer):
    """
        login serializer
    """
    mobile = serializers.CharField(
        allow_blank=False,
        allow_null=False,
        error_messages={'required': 'Please enter a valid mobile.',
                        'blank': 'Please enter a valid mobile.',
                        'null': 'Please enter a valid mobile'}
    )
    password = serializers.CharField(max_length=128)
    user_token = serializers.CharField(max_length=1024, required=False)
    application = serializers.CharField(max_length=1024, required=False)
    device = serializers.CharField(max_length=1024, required=False)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(
        min_length=6,
        max_length=128,
        error_messages={'required': 'Please enter a valid password.',
                        'blank': 'Please enter a valid password.',
                        'null': 'Please enter a valid password.',
                        'min_length': 'Password should have minimum 6 characters.'}
    )


class UserRegistrationSerializer(ModelSerializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """
    email = serializers.EmailField(
        allow_blank=False,
        allow_null=False,
        error_messages={
            'required': 'Please enter a valid e-mail id.',
            'invalid': 'Please enter a valid e-mail id.',
            'blank': 'Please enter a valid e-mail id.',
            'null': 'Please enter a valid e-mail id.'
        },
    )

    class Meta:
        model = User
        fields = ('id', 'email', "password", 'first_name', 'last_name', 'referer_code')
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('id',)

    def validate_password(self, value):
        if len(value) > 5:
            return value
        else:
            msg = _('Password should have minimum 6 characters.')
            raise serializers.ValidationError(msg)


class PasswordResetSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        allow_blank=False,
        allow_null=False,
        error_messages={'required': 'Please enter a valid mobile.',
                        'blank': 'Please enter a valid mobile.',
                        'null': 'Please enter a valid mobile'}
    )


class RoleSerializer(ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'is_active')


class SMS_RecordsSerializers(ModelSerializer):
    class Meta:
        model = SMS_Records
        fields = '__all__'


class PatientLoginSerializer(ModelSerializer):
    class Meta:
        model = PatientLogin
        fields = '__all__'


class StaffLoginSerializer(ModelSerializer):
    class Meta:
        model = StaffLogin
        fields = '__all__'


class TaskLoginSerializer(ModelSerializer):
    class Meta:
        model = TaskLogin
        fields = '__all__'
