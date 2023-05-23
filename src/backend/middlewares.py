from .accounts.models import User, UserFcm
from .appointment.models import Appointment
from .logger_constants import CONST_LOG_GENERATOR
from .patients.models import Patients, ReturnPayment, PatientPayment, PatientInvoices
from .practice.models import ActivityLog, PracticeStaff, Practice, PushNotifications
from .practice.serializers import PushNotificationSerializer
from .utils import timezone
from django.conf import settings
from django.db.models.signals import *
from django.dispatch import receiver
from pyfcm import FCMNotification
from rest_framework.authtoken.models import Token


class LogAllMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global user_id
        global os
        global agent
        global client_app
        global request_uri
        user_id = None
        request_uri = request.META.get('PATH_INFO', None)
        token = request.META.get('HTTP_AUTHORIZATION', None)
        os = request.META.get('HTTP_CLIENT_OS', None)
        if not os:
            os = request.META.get('CLIENT_OS', None)
        client_app = request.META.get('HTTP_CLIENT_APP', None)
        if not client_app:
            client_app = request.META.get('CLIENT_APP', None)
        agent = request.META.get('HTTP_CLIENT_AGENT', None)
        if not agent:
            agent = request.META.get('CLIENT_AGENT', None)
        if token:
            token = token[6:]
            user_obj = Token.objects.filter(key=token).first()
            user_id = user_obj.user if user_obj else None
        return self.get_response(request)

    @receiver(pre_save)
    def add_creator(sender, instance, **kwargs):
        try:
            x = user_id
        except:
            return instance
        if not instance.pk and hasattr(instance, 'created_by') and user_id:
            try:
                instance.created_by = User.objects.get(mobile=user_id)
            except:
                print("Invalid User")
        return instance

    @receiver(post_save)
    def add_activity(sender, instance, created, raw, using, **kwargs):
        for log_obj in CONST_LOG_GENERATOR:
            if sender == log_obj["model_name"]:
                try:
                    user_obj = User.objects.get(mobile=user_id)
                except:
                    return
                category = log_obj["Category"]
                sub_category = log_obj["SubCategory"]
                if created:
                    activity = "Added"
                elif hasattr(instance, 'is_active') and not instance.is_active \
                        and hasattr(instance, 'is_cancelled') and instance.is_cancelled:
                    activity = "Deleted"
                elif instance.is_active:
                    activity = "Modified"
                else:
                    activity = "Deleted"
                # Below check is added to skip problem caused due to .save() used in the same function
                last_log = ActivityLog.objects.filter(component=category, sub_component=sub_category,
                                                      user=user_obj).last()
                if last_log and (timezone.now_local() - last_log.created_at).total_seconds() < 1 and \
                        last_log.created_by == user_obj and (
                        last_log.activity == activity or last_log.activity == "Added"):
                    return
                created_by = instance.created_by if hasattr(instance, 'created_by') else None
                if type(instance) == Patients:
                    patient = instance
                elif hasattr(instance, 'patient'):
                    patient = instance.patient if type(instance.patient) == Patients else None
                elif hasattr(instance, 'patient_id'):
                    patient = instance.patient_id if type(instance.patient_id) == Patients else None
                else:
                    patient = None
                if type(instance) == Practice:
                    practice = instance
                elif hasattr(instance, 'practice'):
                    practice = instance.practice if type(instance.practice) == Practice else None
                elif hasattr(instance, 'practice_id'):
                    practice = instance.practice_id if type(instance.practice_id) == Practice else None
                else:
                    practice = None
                if type(instance) == PracticeStaff:
                    staff = instance
                elif hasattr(instance, 'staff'):
                    staff = instance.staff if type(instance.staff) == PracticeStaff else None
                elif hasattr(instance, 'doctor'):
                    staff = instance.doctor if type(instance.doctor) == PracticeStaff else None
                else:
                    staff = None
                if type(instance) == PatientInvoices:
                    extra = instance.invoice_id
                    if request_uri and ("return" in request_uri or "payment" in request_uri):
                        return
                elif type(instance) == ReturnPayment:
                    extra = instance.return_id
                elif type(instance) == PatientPayment:
                    extra = instance.payment_id
                elif type(instance) == Appointment:
                    extra = instance.schedule_at.date().strftime('%Y-%m-%d')
                else:
                    extra = None
                activity_data = {
                    "patient": patient,
                    "staff": staff,
                    "practice": practice,
                    "component": category,
                    "sub_component": sub_category,
                    "activity": activity,
                    "os": os,
                    "application": client_app,
                    "agent": agent,
                    "user": user_obj,
                    "extra": extra,
                    "record_created_by": created_by
                }
                ActivityLog.objects.create(**activity_data)
        return

    @receiver(post_save, sender=PushNotifications)
    def send_notification(sender, instance, created, raw, using, **kwargs):
        if created:
            queryset = UserFcm.objects.filter(is_active=True)
            if instance.user:
                queryset = queryset.filter(user=instance.user)
            if instance.device:
                queryset = queryset.filter(device=instance.device)
            if instance.application:
                queryset = queryset.filter(application=instance.application)
            extra_notification_kwargs = {
                'image': instance.image_link if instance.image_link else None
            }
            user_tokens = []
            print(queryset)
            for data in queryset:
                user_tokens.append(data.user_token)
            print(user_tokens)
            if len(user_tokens) > 0:
                push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
                extra_data = PushNotificationSerializer(instance).data
                result = push_service.notify_multiple_devices(registration_ids=user_tokens, message_icon=instance.icon,
                                                              message_title=instance.title, message_body=instance.body,
                                                              data_message=extra_data,
                                                              extra_notification_kwargs=extra_notification_kwargs)
                print(result, instance)
