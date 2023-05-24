import logging
import os
import os.path
# Sending Email
from threading import Thread

from ..appointment.models import Appointment
from ..constants import CONST_PRACTICE_DATA, CONST_ORDER_PREFIX
from ..patients.models import Patients
from ..practice.models import EmailCommunications, PracticeStaff
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send(to, subject, html_body, text_body=None, attachments=[], from_email=None, cc=None, bcc=None):
    if not (isinstance(to, list) or isinstance(to, tuple)):
        to = [to]

    # Remove empty items
    to = [x for x in to if x not in (None, "")]

    if text_body is None:
        text_body = strip_tags(html_body)

    # Convert CC into a list
    if cc and not (isinstance(cc, list) or isinstance(cc, tuple)):
        cc = [cc]

    # Convert BCC into a list
    if bcc and not (isinstance(bcc, list) or isinstance(bcc, tuple)):
        bcc = [bcc]

    # if bcc is None, set a default email as bcc
    if not bcc:
        bcc = []

    try:
        msg = EmailMultiAlternatives(subject, text_body, to=to)
        if cc:
            msg.cc = cc

        if bcc:
            msg.bcc = bcc

        if from_email:
            msg.from_email = from_email

        msg.attach_alternative(html_body, "text/html")
        for attachment in attachments:
            if attachment:
                # Try to get only filename from full-path
                try:
                    attachment.open()
                except Exception as e:
                    print(str(e))
                attachment_name = os.path.split(attachment.name)[-1]
                msg.attach(attachment_name or attachment.name, attachment.read())
        msg.send()
        return True
    except Exception:
        logger.exception("Unable to send the mail.")
        return False


def send_from_template(to, subject, template, context, **kwargs):
    # print template
    html_body = render_to_string(template, context)
    return send(to, subject, html_body, **kwargs)


def appointment_email(appointment, appointment_status, cron=False):
    from ..appointment.serializers import AppointmentSerializer
    try:
        appointment_data = Appointment.objects.get(id=appointment.id)
        # appointment_data.practice=1
        # appointment_data.save()
    except:
        return "Invalid Appointment"
    print("App",appointment_data)
    to_send, base_template_url, email_template, email_subject = False, "appointment_email/", "", ""
    doctor = appointment_data.doctor if appointment_data and appointment_data.doctor else None
    patient = appointment_data.patient if appointment_data and appointment_data.patient else None
    email_communications = EmailCommunications.objects.filter(practice=appointment_data.practice.id,
                                                              is_active=True).values().order_by('-id').first()
    if email_communications:
        if appointment_status == "CREATE":
            email_template, email_subject, to_send = (
                base_template_url + "appointment_confirmation.html", 'Your appointment is confirmed', True) if \
                email_communications['appointment_confirmation_email'] else (None, None, False)
        elif appointment_status == "CANCEL":
            email_template, email_subject, to_send = (
                base_template_url + "appointment_cancellation.html", 'Your appointment is cancelled', True) if \
                email_communications['appointment_cancellation_email'] else (None, None, False)
        elif appointment_status == "REMINDER":
            email_template, email_subject, to_send = (
                base_template_url + "appointment_reminder.html", 'Appointment Reminder', True) if email_communications[
                'appointment_reminder_email'] else (None, None, False)
        elif appointment_status == "FOLLOWUP":
            email_template, email_subject, to_send = (
                base_template_url + "appointment_followup.html", 'Appointment FollowUp Required', True) if \
                email_communications['followup_reminder_email'] else (None, None, False)
        else:
            to_send = False
    if to_send and email_template:
        logo_url = settings.DOMAIN + settings.MEDIA_URL + email_communications["clinic_logo"] if email_communications[
            "clinic_logo"] else None
        recipients = []
        is_doctor_alo = PracticeStaff.objects.get(id=appointment_data.doctor.pk) if appointment_data.doctor else ''
        is_patient_alo = Patients.objects.get(id=appointment_data.patient.pk)
        if not cron and is_doctor_alo.confirmation_email:
            recipients.append(doctor.user.email)
        if is_patient_alo.email_enable:
            recipients.append(patient.user.email)
        print('email res:', recipients)
        context = {'data': AppointmentSerializer(appointment_data).data, "logo": logo_url}
        Thread(target=send_from_template, args=(recipients, email_subject, email_template, context)).start()
        return True
    return False


def patient_greeting_email(patient, greet_constant):
    to_send, base_template_url, email_template, email_subject = False, "patient_greeting_email/", "", ""
    if patient.birthday_sms_email:
        if greet_constant == "ANNIVERSARY":
            email_template, email_subject, to_send = base_template_url + "anniversary.html", 'Congratulations on your anniversary', True
        elif greet_constant == "BIRTHDAY":
            email_template, email_subject, to_send = base_template_url + "birthday.html", 'Congratulations on your birthday', True
    if to_send and email_template:
        logo_url = settings.DOMAIN + settings.MEDIA_URL + CONST_PRACTICE_DATA['logo']
        context = {'data': {'user': {'first_name': patient.user.first_name}}, 'logo': logo_url}
        Thread(target=send_from_template, args=([patient.user.email], email_subject, email_template, context)).start()
        return True
    return False


def order_placed_email(sale_obj):
    email_subject = "Order Placed - BK Arogyam & Research Pvt. Ltd."
    email_template = "orders/order_placed.html"
    context = {'data': sale_obj, 'base_url': settings.DOMAIN + settings.MEDIA_URL, 'prefix': CONST_ORDER_PREFIX}
    mail_list = ["sc6500@gmail.com", "sumitbkarogyam@gmail.com", "remercuras@gmail.com"]
    patient_mail = ["bkarogyam44@gmail.com", "doctor@bkarogyam.com"]
    if sale_obj.email:
        patient_mail.append(sale_obj.email)
    Thread(target=send_from_template, args=(mail_list, email_subject, email_template, context)).start()
    Thread(target=send_from_template, args=(patient_mail, email_subject, email_template, context)).start()
    return
