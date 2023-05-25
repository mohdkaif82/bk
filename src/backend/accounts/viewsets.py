import json
import logging
from .models import User
from datetime import datetime
from functools import partial
from urllib.parse import urlencode
from urllib.request import urlopen

from .crons import update_referer
from .models import PasswordResetCode, PatientLogin, StaffLogin, TaskLogin, UserFcm
from .permissions import UserPermissions, PatientLoginPermissions, StaffLoginPermissions
from .serializers import UserSerializer, PermissionSerializer, GroupSerializer, PasswordResetSerializer, \
    SMS_RecordsSerializers, PatientLoginSerializer, StaffLoginSerializer, UserSerializer as UserRestrictedSerializer, \
    TaskLoginSerializer
from .services import _parse_data, auth_login, auth_password_change, auth_register_user, user_clone_api, \
    create_user_token
from ..base import response
from ..base.api.viewsets import ModelViewSet
from ..constants import CONFIG, CONST_REPORT_MAIL
from ..patients.models import Patients
from ..patients.serializers import PatientsSerializer
from ..practice.models import PracticeStaff, PracticeStaffRelation, Practice, PracticeUserPermissions
from ..practice.serializers import PracticeBasicSerializer, \
    PracticeStaffRelationDataSerializer, PracticeUserPermissionsSerializer
from ..utils.sms import send_sms_without_save
from ..utils.timezone import now_local
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import signing
from django.db.models import F
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from .notification import send_noti,send_bulk_notification


logger = logging.getLogger(__name__)

parse_password_reset_data = partial(_parse_data, cls=PasswordResetSerializer)



from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer

class SignupView(APIView):
    def get(self, request):
        users = User.objects.all()
        return Response(users.values(), status=status.HTTP_200_OK)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        print(request.data,"pppppppppppppppppppppppppppp")

        pa=request.data['password']
        if serializer.is_valid():
            # user = User.objects.create_user( password='password')
            ser=serializer.save()
            usr=User.objects.get(id=ser.id)
            usr.set_password(pa)
            usr.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = get_user_model().objects.all()
    permission_classes = (UserPermissions,)
    serializer_class = UserSerializer

    @action(methods=['GET'], detail=False)
    def config(self, request):
        data = {}
        parameters = request.query_params.get("parameters", None)
        param_list = parameters.split(",") if parameters else []
        CONFIG["config_date_time"] = now_local()
        CONFIG["config_date_only"] = now_local(True)
        for parameter in param_list:
            if parameter in CONFIG:
                data[parameter] = CONFIG[parameter]
            else:
                data[parameter] = None
        return response.Ok(data)

    @action(methods=["POST"], detail=False)
    def login(self, request):
        auth_pk = auth_login(request)
    
        user_get = User.objects.get(id=request.user.id)
        token_get = request.POST.get("user_token")
        device_get = request.POST.get("device")
        application_get = request.POST.get("application")
        
        if auth_pk:
            message_body = "thanks for login"
            message_title = "BK Arogyam "
            registration_id = "fqcio3JVdOAY_MBX5R0wZN:APA91bGOut_Q0a4kKjBZFhcqglmYnOPSj3y0gaFDU6muVw77C3xL-pFZNdFV_yA9rZnDsrllVDqQ7YsS37qlgncY7YjXu9f02u46zy-QVR2SiJar-G_7XXew940aTQwqz6-9ihld0ZZi"
            n = UserFcm.objects.get_or_create(user=user_get,
               
                user_token=token_get,
                device=device_get,
                application=application_get,
            )

            # send_noti(
            #     message_body=message_body,
            #     registration_id=registration_id,
            #     message_title=message_title,
            # )

        # send_bulk_notification(data=message_body,registration_ids=registration_id)
        return auth_pk

    @action(methods=['GET'], detail=False)
    def generate_referer(self, request):
        count = update_referer()
        return response.Ok({"count": count})

    @action(methods=['POST'], detail=False)
    def logout(self, request):
        user_token = request.data.get('user_token', None)
        device = request.data.get('device', None)
        application = request.data.get('application', None)
        Token.objects.filter(user=request.user).delete()
        UserFcm.objects.filter(user_token=user_token, device=device, application=application).delete()
        logout(request)
        return response.Ok({"detail": "Successfully logged out."})

    @action(methods=['POST'], detail=False)
    def passwordchange(self, request):
        data = auth_password_change(request)
        user, new_password = request.user, data.get('new_password')
        if user.check_password(data.get('old_password')):
            user.set_password(new_password)
            user.save()
            content = {'success': 'Password changed successfully.'}
            return response.Ok(content)
        else:
            content = {'detail': 'Old password is incorrect.'}
            return response.BadRequest(content)

    @action(methods=['POST'], detail=False)
    def register(self, request):
        data = auth_register_user(request)
        
        return response.Created(data)

    @action(methods=['POST'], detail=True)
    def deactivate(self, request):
        user = self.get_object()
        is_active = request.data('is_active')
        user.is_active = is_active
        user.save()
        content = {'success': 'User Deactivted successfully.'}
        return response.Ok(content)

    @action(methods=['GET'], detail=False)
    def permission_group(self, request):
        return_dict = {
            "groups": GroupSerializer(Group.objects.all(), many=True).data,
            "permissions": PermissionSerializer(Permission.objects.all(), many=True).data
        }
        return response.Ok(return_dict)

    @action(methods=['GET'], detail=False)
    def user_clone(self, request):
        practice = request.query_params.get("practice")
        if not request.user.is_authenticated:
            content = {'detail': 'user is not authenticated'}
            return response.BadRequest(content)
        return response.Ok(user_clone_api(request.user, practice))

    @action(methods=['GET'], detail=False)
    def all_permissions(self, request):
        from ..constants import ROLES_PERMISSIONS, GLOBAL_PERMISSIONS
        all_permissions = ROLES_PERMISSIONS + GLOBAL_PERMISSIONS
        categories = []
        for permission in all_permissions:
            module = permission.get("module", None)
            if module not in categories:
                categories.append(module)
        return response.Ok({
            "practice_permissions": ROLES_PERMISSIONS,
            "global_permissions": GLOBAL_PERMISSIONS,
            "categories": categories
        })

    @action(methods=['GET'], detail=False)
    def reports_mail(self, request):
        all_mail = PracticeUserPermissions.objects.filter(staff__is_active=True, codename=CONST_REPORT_MAIL,
                                                          is_active=True).values(
            "staff__user__first_name", "staff__user__email").annotate(name=F("staff__user__first_name"),
                                                                      email=F("staff__user__email")).values("name",
                                                                                                            "email")
        super_users = PracticeStaff.objects.filter(user__is_superuser=True).values(
            'user__first_name', 'user__email').annotate(name=F("user__first_name"), email=F("user__email")).values(
            "name", "email")
        result = list(super_users) + list(all_mail)
        res_list = []
        for i in range(len(result)):
            if result[i] not in result[i + 1:]:
                res_list.append(result[i])
        return response.Ok(res_list)

    @action(methods=['GET'], detail=False)
    def registered_list(self, request):
        users = get_user_model().objects.filter(is_active=False)
        serializer = UserSerializer(users, many=True)
        return response.Ok(serializer.data)

    @action(methods=['GET'], detail=False)
    def referer(self, request):
        code = request.query_params.get("code", None)
        user = get_user_model().objects.filter(referer_code=code, is_active=True).exclude(patients=None).first()
        if user:
            patient = Patients.objects.filter(user=user, is_active=True).first()
            data = {
                "user_exists": True,
                "name": user.first_name,
                "practice": patient.practice.pk if patient and patient.practice else None,
                "role": patient.role.pk if patient and patient.role else None
            }
        else:
            data = {
                "user_exists": False
            }
        return response.Ok(data)

    @action(methods=['POST'], detail=False)
    def staff_reset_mail(self, request):
        from ..accounts.models import User
        data = parse_password_reset_data(request.data)
        mobile = data.get('mobile')
        if User.objects.filter(mobile=mobile).exists():
            try:
                user = get_user_model().objects.get(mobile=mobile)
                email = user.email
                password_reset_code = PasswordResetCode.objects.create_reset_code(user)
                password_reset_code.send_password_reset_email()
                message = "We have sent a password reset link to the {}. Use that link to set your new password".format(
                    email)
                return response.Ok({"detail": message})
            except get_user_model().DoesNotExist:
                message = "Email '{}' is not registered with us. Please provide a valid email id".format(email)
                message_dict = {'detail': message}
                return response.BadRequest(message_dict)
            except Exception:
                message = "Unable to send password reset link to email-id- {}".format(email)
                message_dict = {'detail': message}
                logger.exception(message)
                return response.BadRequest(message_dict)
        else:
            message = {'detail': 'User for this staff does not exist'}
            return response.BadRequest(message)

    @action(methods=['GET'], detail=False)
    def sms_status_update(self, request):
        import requests, re
        from ..accounts.models import SMS_Records
        user = request.GET['user'] if 'user' in request.GET else None
        pending_SMS = SMS_Records.objects.filter(status="PENDING").all()
        for sms in pending_SMS:
            try:
                status_response = requests.get(
                    "http://www.smsjust.com/blank/sms/user/response.php?%20Scheduleid=" + sms.request_id)
                status = status_response.text.strip().split()[1] if len(status_response.text.strip().split()) > 1 else \
                    status_response.text.strip().split()[0]
                status = re.compile(r'<[^>]+>').sub('', status)
                SMS_Records.objects.filter(id=sms.id).update(status=status)
            except:
                print(sms, "failed")
        user_sms = SMS_RecordsSerializers(SMS_Records.objects.filter(user__id=user).order_by("-created_at"),
                                          many=True).data
        return response.Ok({"success": "true", "user_sms": user_sms})

    @action(methods=['GET', 'POST'], detail=True)
    def task_login(self, request, *args, **kwargs):
        user = self.get_object()
        if request.method == 'GET':
            data = TaskLogin.objects.filter(is_active=True)
            if user:
                data = data.filter(user=user)
            return response.Ok(TaskLoginSerializer(data.order_by("-id").first()).data)
        else:
            data = request.data.copy()
            login_id = data.pop("id", None)
            data["user"] = user.pk
            if login_id:
                login_obj = TaskLogin.objects.get(id=login_id)
                serializer = TaskLoginSerializer(instance=login_obj, data=data, partial=True)
            else:
                serializer = TaskLoginSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(TaskLoginSerializer(instance=update_response).data)

    @action(methods=['POST'], detail=False)
    def reset_password(self, request):
        code = request.data.get('code')
        password = request.data.get('password')
        if code:
            try:
                password_reset_code = PasswordResetCode.objects.get(code=code.encode('utf8'))
                uid = force_text(urlsafe_base64_decode(password_reset_code.uid))
                password_reset_code.user = get_user_model().objects.get(id=uid)
            except:
                message = 'Unable to verify user.'
                message_dict = {'detail': message}
                return response.BadRequest(message_dict)
            # verify signature with the help of timestamp and previous password for one secret urls of password reset.
            else:
                signer = signing.TimestampSigner()
                max_age = settings.PASSWORD_RESET_TIME
                l = (password_reset_code.user.password, password_reset_code.timestamp, password_reset_code.signature)
                try:
                    signer.unsign(':'.join(l), max_age=max_age)
                except (signing.BadSignature, signing.SignatureExpired):
                    logger.info('Session Expired')
                    message = 'Password reset link expired. Please re-generate password reset link. '
                    message_dict = {'detail': message}
                    return response.BadRequest(message_dict)
            password_reset_code.user.set_password(password)
            password_reset_code.user.save()
            message = "Password Created successfully"
            message_dict = {'detail': message}
            return response.Ok({"success": message_dict})
        else:
            message = {'detail': 'Password reset link expired. Please re-generate password reset link. '}
            return response.BadRequest(message)


class PatientLoginViewSet(ModelViewSet):
    serializer_class = PatientLoginSerializer
    queryset = PatientLogin.objects.all()
    permission_classes = ()
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        return []

    @action(methods=['POST'], detail=False)
    def resend_otp(self, request):
        import datetime
        mobile = request.data.get("phone_no")
        patient = Patients.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if patient:
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
            login_obj = PatientLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=timestamp,
                                                    resend_counter__gt=0).first()
            if login_obj:
                send_sms_without_save(mobile, "Your OTP for Patient Login is " + str(
                    login_obj.otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
                login_obj.resend_counter = login_obj.resend_counter - 1
                login_obj.save()
                return response.Ok({"detail": "OTP resent successfully"})
            else:
                return response.BadRequest(
                    {"detail": "Maximum retries have been exceeded. Please retry after 15 minutes."})
        else:
            return response.BadRequest({"detail": "No Such Patient with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def resend_registration(self, request):
        import datetime
        if not self.verify_google_recaptcha(request):
            return response.BadRequest({"detail": "Suspicious attempt Blocked"})
        mobile = request.data.get("phone_no")
        timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
        login_obj = PatientLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=timestamp,
                                                resend_counter__gt=0).first()
        if login_obj:
            send_sms_without_save(mobile, "Your OTP for Registration is " + str(
                login_obj.otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
            login_obj.resend_counter = login_obj.resend_counter - 1
            login_obj.save()
            return response.Ok({"detail": "OTP resent successfully"})
        else:
            return response.BadRequest(
                {"detail": "Maximum retries have been exceeded. Please retry after 15 minutes."})

    @action(methods=['POST'], detail=False)
    def send_otp(self, request):
        from datetime import date
        mobile = request.data.get("phone_no")
        patient = Patients.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if patient:
            otp = self.get_random_number(6)
            PatientLogin.objects.filter(phone_no=mobile, modified_at__lt=date.today()).delete()
            login_obj = PatientLogin.objects.filter(phone_no=mobile, is_active=True,
                                                    modified_at__gte=date.today()).first()
            if login_obj:
                counter = login_obj.counter - 1
                if counter > 0:
                    PatientLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=date.today()).update(
                        otp=otp, is_active=True, counter=counter, resend_counter=25, modified_at=datetime.now())
            else:
                counter = 25
                PatientLogin.objects.create(phone_no=mobile, otp=otp)
            if counter > 0:
                send_sms_without_save(mobile, "Your OTP for Patient Login is " + str(
                    otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
                return response.Ok({"detail": "OTP sent successfully"})
            else:
                return response.BadRequest({"detail": "Max tries for OTP exceeded. Kindly try again tommorow."})
        else:
            return response.BadRequest({"detail": "No Such Patient with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def registration_otp(self, request):
        from datetime import date
        if not self.verify_google_recaptcha(request):
            return response.BadRequest({"detail": "Suspicious attempt Blocked"})
        mobile = request.data.get("phone_no")
        PatientLogin.objects.filter(phone_no=mobile, modified_at__lt=date.today()).delete()
        login_obj = PatientLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=date.today()).first()
        otp = self.get_random_number(6)
        if login_obj:
            counter = login_obj.counter - 1
            if counter > 0:
                PatientLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=date.today()).update(
                    otp=otp, is_active=True, counter=counter, resend_counter=25, modified_at=datetime.now())
        else:
            counter = 25
            PatientLogin.objects.create(phone_no=mobile, otp=otp)
        if counter > 0:
            send_sms_without_save(mobile,
                                  "Your OTP for Registration is " + str(otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
            return response.Ok({"detail": "OTP sent successfully"})
        else:
            return response.BadRequest({"detail": "Max tries for OTP exceeded. Kindly try again tommorow."})

    @action(methods=['POST'], detail=False)
    def verify_otp(self, request):
        import datetime
        mobile = request.data.get("phone_no")
        otp = request.data.get("otp")
        user_token = request.data.get('user_token', None)
        device = request.data.get('device', None)
        application = request.data.get('application', None)
        patient = Patients.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if patient:
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
            login_obj = PatientLogin.objects.filter(phone_no=mobile, otp=otp, is_active=True,
                                                    modified_at__gte=timestamp).first()
            if login_obj:
                login_obj.is_active = False
                login_obj.save()
                token, created = Token.objects.get_or_create(user=patient.user)
                login(request, patient.user)
                create_user_token(user_token, device, application, patient.user)
                return response.Ok({"patient": PatientsSerializer(patient).data, "token": token.key})
            else:
                return response.BadRequest({"detail": "Invalid OTP used. Please Check!!"})
        else:
            return response.BadRequest({"detail": "No Such Patient with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def switch(self, request):
        if request.user.is_superuser:
            mobile = request.data.get("phone_no")
            patient = Patients.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
            if patient:
                token, created = Token.objects.get_or_create(user=patient.user)
                login(request, patient.user)
                return response.Ok({"patient": PatientsSerializer(patient).data, "token": token.key})
            else:
                return response.BadRequest({"detail": "No Such Patient with mobile no: " + str(mobile) + " exists."})
        else:
            return response.Unauthorized({"detail": "Security violation. This will be reported!"})

    @action(methods=['POST'], detail=False)
    def registration_verify(self, request):
        import datetime
        if not self.verify_google_recaptcha(request):
            return response.BadRequest({"detail": "Suspicious attempt Blocked"})
        mobile = request.data.get("phone_no")
        otp = request.data.get("otp")
        timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
        login_obj = PatientLogin.objects.filter(phone_no=mobile, otp=otp, is_active=True,
                                                modified_at__gte=timestamp).first()
        if login_obj:
            login_obj.is_active = False
            login_obj.save()
            return response.Ok({"verify": True, "detail": "Mobile Verified"})
        else:
            return response.BadRequest({"verify": False, "detail": "Invalid OTP used. Please Check!!"})

    def get_random_number(self, N):
        from random import randint
        '''
        :param N: No of Digits
        :return: Random number of N digit
        '''

        range_start = 10 ** (N - 1)
        range_end = (10 ** N) - 1
        return randint(range_start, range_end)

    def verify_google_recaptcha(self, request):
        uri_recaptcha = 'https://www.google.com/recaptcha/api/siteverify'
        recaptcha_response = request.data.get('recaptcha_token')
        private_recaptcha = ''
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        params = urlencode({
            'secret': private_recaptcha,
            'response': recaptcha_response,
            'remote_ip': ip,
        })
        data = urlopen(uri_recaptcha, params.encode('utf-8')).read().decode('utf-8')
        result = json.loads(data)
        success = result.get('success', None)
        return success


class StaffLoginViewSet(ModelViewSet):
    serializer_class = StaffLoginSerializer
    queryset = StaffLogin.objects.all()
    permission_classes = (StaffLoginPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        return []

    @action(methods=['POST'], detail=False)
    def resend_otp(self, request):
        import datetime
        mobile = request.data.get("phone_no")
        staff = PracticeStaff.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if staff:
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
            login_obj = StaffLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=timestamp,
                                                  resend_counter__gt=0).first()
            if login_obj:
                send_sms_without_save(mobile, "Your OTP for Staff/Doctor Login is " + str(
                    login_obj.otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
                login_obj.resend_counter = login_obj.resend_counter - 1
                login_obj.save()
                return response.Ok({"detail": "OTP resent successfully"})
            else:
                return response.BadRequest(
                    {"detail": "Maximum retries have been exceeded. Please retry after 15 minutes."})
        else:
            return response.BadRequest({"detail": "No Such Staff/Doctor with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def send_otp(self, request):
        from datetime import date
        mobile = request.data.get("phone_no")
        staff = PracticeStaff.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if staff:
            otp = self.get_random_number(6)
            StaffLogin.objects.filter(phone_no=mobile, modified_at__lt=date.today(), is_active=True).delete()
            login_obj = StaffLogin.objects.filter(phone_no=mobile, is_active=True,
                                                  modified_at__gte=date.today()).first()
            if login_obj:
                counter = login_obj.counter - 1
                if counter > 0:
                    StaffLogin.objects.filter(phone_no=mobile, is_active=True, modified_at__gte=date.today()).update(
                        otp=otp, is_active=True, counter=counter, resend_counter=25, modified_at=datetime.now())
            else:
                counter = 25
                StaffLogin.objects.create(phone_no=mobile, otp=otp)
            if counter > 0:
                send_sms_without_save(mobile, "Your OTP for Staff/Doctor Login is " + str(
                    otp) + ". It is valid for next 10 minutes.\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED")
                return response.Ok({"detail": f"OTP sent successfully {otp}"})
            else:
                return response.BadRequest(
                    {"detail": "Max tries for OTP exceeded. Kindly try again tommorow or login with password"})
        else:
            return response.BadRequest({"detail": "No Such Staff/Doctor with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def verify_otp(self, request):
        import datetime
        mobile = request.data.get("phone_no")
        otp = request.data.get("otp")
        user_token = request.data.get('user_token', None)
        device = request.data.get('device', None)
        application = request.data.get('application', None)
        staff = PracticeStaff.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
        if staff:
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=15)
            login_obj = StaffLogin.objects.filter(phone_no=mobile, otp=otp, is_active=True,
                                                  modified_at__gte=timestamp).first()
            if login_obj:
                login_obj.is_active = False
                login_obj.save()
                token, created = Token.objects.get_or_create(user=staff.user)
                login(request, staff.user)
                user = staff.user
                if user.is_superuser:
                    practice_list = []
                    practices = PracticeBasicSerializer(Practice.objects.filter(is_active=True),
                                                        many=True).data
                    for practice in practices:
                        practice_list.append({"practice": practice, "staff": staff.pk})
                else:
                    practice_list = PracticeStaffRelationDataSerializer(
                        PracticeStaffRelation.objects.filter(is_active=True, staff=staff), many=True).data
                practice_id = practice_list[0]["practice"]["id"] if len(practice_list) > 0 and "practice" in \
                                                                    practice_list[0] and "id" in practice_list[0][
                                                                        "practice"] else None
                staff_id = staff.pk
                if practice_id:
                    permissions = PracticeUserPermissionsSerializer(
                        PracticeUserPermissions.objects.filter(staff=staff_id, practice=practice_id, is_active=True),
                        many=True).data
                else:
                    permissions = []
                global_permissions = PracticeUserPermissionsSerializer(
                    PracticeUserPermissions.objects.filter(staff=staff_id, practice=None, is_active=True),
                    many=True).data
                auth_data = {
                    "token": token.key,
                    "user": UserRestrictedSerializer(user, context={'request': request}).data,
                    "practice_list": practice_list,
                    "first_permissions": permissions,
                    "global_permissions": global_permissions
                }
                create_user_token(user_token, device, application, user)
                return response.Ok(auth_data)
            else:
                return response.BadRequest({"detail": "Invalid OTP used. Please Check!!"})
        else:
            return response.BadRequest({"detail": "No Such Staff/Doctor with mobile no: " + str(mobile) + " exists."})

    @action(methods=['POST'], detail=False)
    def switch(self, request):
        if request.user.is_superuser:
            mobile = request.data.get("phone_no")
            staff = PracticeStaff.objects.filter(is_active=True, user__mobile=mobile, user__is_active=True).first()
            if staff:
                token, created = Token.objects.get_or_create(user=staff.user)
                login(request, staff.user)
                user = staff.user
                if user.is_superuser:
                    practice_list = []
                    practices = PracticeBasicSerializer(Practice.objects.filter(is_active=True),
                                                        many=True).data
                    for practice in practices:
                        practice_list.append({"practice": practice, "staff": staff.pk})
                else:
                    practice_list = PracticeStaffRelationDataSerializer(
                        PracticeStaffRelation.objects.filter(is_active=True, staff=staff), many=True).data
                practice_id = practice_list[0]["practice"]["id"] if len(practice_list) > 0 and "practice" in \
                                                                    practice_list[0] and "id" in practice_list[0][
                                                                        "practice"] else None
                staff_id = staff.pk
                if practice_id:
                    permissions = PracticeUserPermissionsSerializer(
                        PracticeUserPermissions.objects.filter(staff=staff_id, practice=practice_id, is_active=True),
                        many=True).data
                else:
                    permissions = []
                global_permissions = PracticeUserPermissionsSerializer(
                    PracticeUserPermissions.objects.filter(staff=staff_id, practice=None, is_active=True),
                    many=True).data
                auth_data = {
                    "token": token.key,
                    "user": UserRestrictedSerializer(user, context={'request': request}).data,
                    "practice_list": practice_list,
                    "first_permissions": permissions,
                    "global_permissions": global_permissions
                }
                return response.Ok(auth_data)
            else:
                return response.BadRequest(
                    {"detail": "No Such Staff/Doctor with mobile no: " + str(mobile) + " exists."})
        else:
            return response.Unauthorized({"detail": "Security violation. This will be reported!"})

    def get_random_number(self, N):
        from random import randint
        '''
        :param N: No of Digits
        :return: Random number of N digit
        '''

        range_start = 10 ** (N - 1)
        range_end = (10 ** N) - 1
        return randint(range_start, range_end)
