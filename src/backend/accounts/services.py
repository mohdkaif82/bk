from collections import namedtuple
from functools import partial

from .models import UserFcm
from .serializers import LoginSerializer as LoginRestrictedSerializer, \
    UserSerializer as UserRestrictedSerializer, PasswordChangeSerializer, UserRegistrationSerializer
from ..base import response
from ..practice.models import Practice, PracticeStaffRelation, PracticeStaff
from ..practice.serializers import PracticeStaffRelationDataSerializer, PracticeBasicDataSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

User = namedtuple('User', ['email', 'password', 'first_name', 'last_name','mobile'])


def _parse_data(data, cls):
    """
    Generic function for parse user data using
    specified validator on `cls` keyword parameter.
    Raises: ValidationError exception if
    some errors found when data is validated.
    Returns the validated data.
    """
    serializer = cls(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer.validated_data


# Parse Auth login data
parse_auth_login_data = partial(_parse_data, cls=LoginRestrictedSerializer)
parse_auth_password_change_data = partial(_parse_data, cls=PasswordChangeSerializer)
parse_register_user_data = partial(_parse_data, cls=UserRegistrationSerializer)


def create_user_token(user_token, device, application, user):
    if user_token and device and application and user:
        if UserFcm.objects.filter(user_token=user_token, device=device, application=application,
                                  is_active=True).exists():
            UserFcm.objects.filter(user_token=user_token, device=device, application=application,
                                   is_active=True).update(user=user)
        else:
            UserFcm.objects.create(user=user, user_token=user_token, device=device, application=application)


def auth_login(request):
    """
    params: request
    return: token, password
    """
    data, auth_data = parse_auth_login_data(request.data), None

    email, password = data.get('mobile'), data.get('password')
    user_token = data.get('user_token', None)
    device = data.get('device', None)
    application = data.get('application', None)
    if email and password:
        from ..practice.models import PracticeUserPermissions
        user = authenticate(username=email, password=password)
        if user:
            if not user.is_active:
                return response.BadRequest({'detail': 'User account is disabled.'})
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            staff = PracticeStaff.objects.get(user=user, is_active=True, user__is_active=True)
            if user.is_superuser:
                practice_list = []
                practices = PracticeBasicDataSerializer(Practice.objects.filter(is_active=True),
                                                        many=True).data
                for practice in practices:
                    practice_list.append({"practice": practice, "staff": staff.pk})
            else:
                practice_list = PracticeStaffRelationDataSerializer(
                    PracticeStaffRelation.objects.filter(is_active=True, staff=staff), many=True).data
            auth_data = {
                "token": token.key,
                "user": UserRestrictedSerializer(user, context={'request': request}).data,
                "practice_list": practice_list
            }
            create_user_token(user_token, device, application, user)
            return response.Ok(auth_data)
        else:
            return response.BadRequest({'detail': 'Incorrect Email and password.'})
    else:
        return response.BadRequest({'detail': 'Must Include Email and password.'})


def auth_password_change(request):
    """
    params: request
    return: data
    """
    data = parse_auth_password_change_data(request.data)
    return data


def user_clone_api(user, practice):
    from ..practice.serializers import PracticeUserPermissionsSerializer, PracticeStaffBasicSerializer
    from ..practice.models import PracticeUserPermissions
    from ..constants import ROLES_PERMISSIONS, GLOBAL_PERMISSIONS
    from ..patients.models import Patients
    from ..patients.serializers import PatientsSerializer
    staff = PracticeStaff.objects.filter(user=user, is_active=True, user__is_active=True).first()
    patient = Patients.objects.filter(user=user, is_active=True, user__is_active=True).first()
    practice_list, permissions, global_perms = [], [], []
    if staff and user.is_superuser:
        permissions = ROLES_PERMISSIONS
        global_perms = GLOBAL_PERMISSIONS
        practices = PracticeBasicDataSerializer(Practice.objects.filter(is_active=True),
                                                many=True).data
        for practice in practices:
            practice_list.append({"practice": practice, "staff": staff.pk})
    elif staff:
        practice_list = PracticeStaffRelationDataSerializer(
            PracticeStaffRelation.objects.filter(is_active=True, staff=staff), many=True).data
        if PracticeStaffRelation.objects.filter(staff=staff, practice=practice, is_active=True).exists():
            permissions = PracticeUserPermissionsSerializer(
                PracticeUserPermissions.objects.filter(staff=staff, practice=practice, is_active=True), many=True).data
            global_perms = PracticeUserPermissionsSerializer(
                PracticeUserPermissions.objects.filter(staff=staff, practice=None, is_active=True), many=True).data
        else:
            permissions = []
            global_perms = []
    auth_data = {
        "user": UserRestrictedSerializer(instance=user).data,
        "practice_list": practice_list,
        "practice_permissions": permissions,
        "global_permissions": global_perms,
        "patient": PatientsSerializer(patient).data if patient else None,
        "staff": PracticeStaffBasicSerializer(staff).data if staff else None
    }
    return auth_data


def auth_register_user(request):
    """
    params: request
    return: user
    """
    UserModel = get_user_model()
    # User details to create an user
    data = parse_register_user_data(request.data)
    user_data = User(
        email=data.get('email'),
        password=data.get('password'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        mobile=request.POST.get('mobile'),
    )
    print(user_data,'mobile',request.POST.get('mobile'))

    user = None
    # Check email is register as a active user
    try:
        user = get_user_model().objects.get(email=data.get('email'), is_active=True)
    except get_user_model().DoesNotExist:
        pass

    # if user is not exist, create a Inactive user
    if not user:
        un_active_user = UserModel.objects.filter(email=user_data.email, is_active=False)
        if un_active_user:
            UserModel.objects.filter(email=user_data.email, is_active=False).delete()

        user = UserModel.objects.create_user(**dict(user_data._asdict()))

    if user and request.POST.get('referer_code') and UserModel.objects.filter(referer_code=request.POST.get('referer_code')).exists():
        user.referer = UserModel.objects.filter(referer_code=request.POST.get('referer_code'))[0]
        user.save()

    return request.data


def auth_register_doctor(request):
    """
    params: request
    return: user
    """
    UserModel = get_user_model()
    # User details to create an user
    data = parse_register_user_data(request.data)
    print('data print kro',data)
    password=data.get('password')
    user_data = User(
        email=data.get('email'),
        password=data.get('password'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        mobile=request.POST.get('mobile'),
    )
    print(user_data,'mobile',request.POST.get('mobile'))

    user = None
    # Check email is register as a active user
    try:
        user = get_user_model().objects.get(email=data.get('email'), is_active=True)
    except get_user_model().DoesNotExist:
        pass

    # if user is not exist, create a Inactive user
    if not user:
        un_active_user = UserModel.objects.filter(email=user_data.email, is_active=False)
        if un_active_user:
            UserModel.objects.filter(email=user_data.email, is_active=False).delete()

        user = UserModel.objects.create_user(**dict(user_data._asdict()))
        print(user)
        # user.set_password(password)
        # user.save()

    if user and data.get('referer_code') and User.objects.filter(referer_code=data.get('referer_code')).exists():
        user.referer = User.objects.filter(referer_code=data.get('referer_code'))[0]
        user.save()
        
    PracticeStaff.objects.get_or_create(user=user,department=data.get('department'),\
        designation=data.get('designation'))

    return request.data


