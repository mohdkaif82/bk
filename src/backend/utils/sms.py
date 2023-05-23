import re
import urllib.parse
from datetime import datetime

import pytz
import requests
from ..accounts.models import User, SMS_Records
from ..appointment.models import Appointment
from ..billing.serializers import PatientPaymentSerializer
from ..constants import CONST_PATIENTS, CONST_WISH_SMS
from ..patients.models import PatientsPromoCode, Patients, PatientPayment
from ..practice.models import Communications


def send_sms_without_save(phone_no, body):
    msgtype='TXT' if len(body) == len(body.encode()) else 'UNI'
    requests.get(
        "http://www.smsjust.com/blank/sms/user/urlsms.php?username=&pass=&response=Y&msgtype="+msgtype+"&senderid=BKARYM&dest_mobileno=" + str(
            phone_no) + "&message=" + urllib.parse.quote(str(body)))


def send_sms(phone_no, body, sms_type):
    msgtype='TXT' if len(body) == len(body.encode()) else 'UNI'
    user = User.objects.get(mobile=phone_no)
    response = requests.get(
        "http://www.smsjust.com/blank/sms/user/urlsms.php?username=&pass=&response=Y&msgtype="+msgtype+"&senderid=BKARYM&dest_mobileno=" + str(
            phone_no) + '&message=' + urllib.parse.quote(str(body)))
    request_id = response.text.strip()
    status_response = requests.get("http://www.smsjust.com/blank/sms/user/response.php?%20Scheduleid=" + request_id)
    status = status_response.text.strip().split()[1] if len(status_response.text.strip().split()) > 1 else \
        status_response.text.strip().split()[0]
    status = re.compile(r'<[^>]+>').sub('', status)
    SMS_Records.objects.create(user=user, status=status, request_id=request_id, body=body, mobile=phone_no,
                               sms_type=sms_type)


def prepare_appointment_sms(appointment, appointment_status):
    from ..practice.services import send_notification
    try:
        appointment_data = Appointment.objects.get(id=appointment.id)
    except:
        message = "Invalid Appointment"
        return message
    to_send = True
    if appointment_data and appointment_data.practice and appointment_data.practice.language:
        practice_language = appointment_data.practice.language
    else:
        return
    doctor = appointment_data.doctor if appointment_data and appointment_data.doctor else None
    language = appointment_data.patient.language if appointment_data and appointment_data.patient \
                                                    and appointment_data.patient.language else practice_language
    communications = Communications.objects.filter(practice=appointment_data.practice.id, sms_language=language,
                                                   is_active=True).values().order_by('-id').first()
    if communications:
        send_message = ""
        if appointment_status == "CREATE":
            if communications['appointment_confirmation_sms']:
                send_message = communications['appointment_confirmation_text']
            else:
                to_send = False
        elif appointment_status == "UPDATE":
            if communications['appointment_confirmation_sms']:
                send_message = communications['appointment_confirmation_text']
            else:
                to_send = False
        elif appointment_status == "CANCEL":
            if communications['appointment_cancellation_sms']:
                send_message = communications['appointment_cancellation_text']
            else:
                to_send = False
        elif appointment_status == "REMINDER":
            if communications['appointment_reminder_sms']:
                send_message = communications['appointment_reminder_text']
            else:
                to_send = False
        elif appointment_status == "FOLLOWUP":
            if communications['follow_up_reminder_sms']:
                send_message = communications['follow_up_reminder_text']
            else:
                to_send = False
        elif appointment_status == "MEDICINE":
            if communications['medicine_renew_sms']:
                send_message = communications['medicine_renew_text']
            else:
                to_send = False
        else:
            to_send = False
        if communications and to_send and send_message:
            if "{{PATIENT}}" in send_message:
                send_message = send_message.replace('{{PATIENT}}', appointment_data.patient.user.first_name)
            if "{{DATE}}" in send_message:
                send_message = send_message.replace('{{DATE}}',
                                                    appointment_data.schedule_at.date().strftime('%d-%m-%Y'))
            if "{{TIME}}" in send_message:
                tz = pytz.timezone('Asia/Kolkata')
                send_message = send_message.replace('{{TIME}}',
                                                    appointment_data.schedule_at.astimezone(tz).time().strftime(
                                                        '%I:%M %p'))
            if "{{CATEGORY}}" in send_message and appointment_data.category:
                send_message = send_message.replace('{{CATEGORY}}', appointment_data.category.name)
            elif "{{CATEGORY}}" in send_message:
                send_message = send_message.replace('{{CATEGORY}}', "")
            if "{{CLINIC}}" in send_message:
                send_message = send_message.replace('{{CLINIC}}', communications['sms_clinic_name'])
            if "{{PATIENT_ID}}" in send_message:
                send_message = send_message.replace('{{PATIENT_ID}}', str(
                    appointment_data.patient.custom_id) if appointment_data.patient.custom_id else str(
                    appointment_data.patient.id))
            if "{{CLINICCONTACTNUMBER}}" in send_message:
                send_message = send_message.replace('{{CLINICCONTACTNUMBER}}', communications['contact_number'])
            if appointment_status in ["CREATE", "UPDATE", "CANCEL", "REMINDER"]:
                send_sms(appointment_data.patient.user.mobile, send_message, "APPOINTMENT")
                if appointment_status == "CREATE":
                    title = "New Appointment Created"
                elif appointment_status == "CANCEL":
                    title = "Appointment Cancelled"
                else:
                    title = "Appointment Update"
                send_notification(appointment_data.patient.user, appointment_data.practice.pk, CONST_PATIENTS, title,
                                  send_message, "APPOINTMENT")
                if doctor and doctor.confirmation_sms:
                    send_sms_without_save(doctor.user.mobile, send_message)
            elif appointment_status == "FOLLOWUP":
                send_sms(appointment_data.patient.user.mobile, send_message, "FOLLOW UP")
                title = "Follow Up Reminder"
                send_notification(appointment_data.patient.user, appointment_data.practice.pk, CONST_PATIENTS, title,
                                  send_message, "APPOINTMENT")
            elif appointment_status == "MEDICINE":
                send_sms(appointment_data.patient.user.mobile, send_message, "MEDICINE RENEWAL")
                title = "Medicine Reminder"
                send_notification(appointment_data.patient.user, appointment_data.practice.pk, CONST_PATIENTS, title,
                                  send_message, "APPOINTMENT")
    return


def prepare_promo_code_sms(promo_code):
    try:
        promo_code_data = PatientsPromoCode.objects.get(id=promo_code.id, is_active=True)
    except:
        return {"detail": "Invalid Promo Code", "error": True}
    to_send = True
    if promo_code_data and promo_code_data.practice:
        practice_language = promo_code_data.practice.language
    else:
        return {"detail": "Invalid Practice in Promo Code", "error": True}
    patients = promo_code_data.patients.all() if len(promo_code_data.patients.all()) > 0 else Patients.objects.all()
    for patient in patients:
        language = patient.language if patient and patient.language else practice_language
        communications = Communications.objects.filter(practice=promo_code_data.practice.id, sms_language=language,
                                                       is_active=True).values().order_by('-id').first()
        if communications:
            if promo_code_data.code_type == "INR":
                send_message = communications['promo_code_value_text']
            elif promo_code_data.code_type == "%":
                send_message = communications['promo_code_percent_text']
                if send_message and "{{MAX_VALUE}}" in send_message and promo_code_data.maximum_discount:
                    send_message = send_message.replace('{{MAX_VALUE}}', str(promo_code_data.maximum_discount))
            else:
                send_message = None
                to_send = False
            if not patient.user.mobile:
                to_send = False
            if communications and to_send and send_message:
                if "{{PATIENT}}" in send_message:
                    send_message = send_message.replace('{{PATIENT}}', patient.user.first_name)
                if "{{CLINIC}}" in send_message:
                    send_message = send_message.replace('{{CLINIC}}', communications['sms_clinic_name'])
                if "{{EXPIRY}}" in send_message and promo_code_data.expiry_date:
                    send_message = send_message.replace('{{EXPIRY}}', promo_code_data.expiry_date.strftime('%d-%m-%Y'))
                if "{{VALUE}}" in send_message and promo_code_data.code_value:
                    send_message = send_message.replace('{{VALUE}}', str(promo_code_data.code_value))
                if "{{MIN_PURCHASE}}" in send_message and promo_code_data.minimum_order:
                    send_message = send_message.replace('{{MIN_PURCHASE}}', str(promo_code_data.minimum_order))
                if "{{CODE}}" in send_message and promo_code_data.promo_code:
                    send_message = send_message.replace('{{CODE}}', str(promo_code_data.promo_code))
                if "{{PATIENT_ID}}" in send_message:
                    send_message = send_message.replace('{{PATIENT_ID}}',
                                                        str(patient.custom_id) if patient.custom_id else str(
                                                            patient.id))
                if "{{CLINICCONTACTNUMBER}}" in send_message:
                    send_message = send_message.replace('{{CLINICCONTACTNUMBER}}', communications['contact_number'])

                send_sms(patient.user.mobile, send_message, "PROMO CODE")
    promo_code_data.sms_sent = True
    promo_code_data.save()
    return {"detail": "Promo Code SMS Sent Successfully", "error": False}


def prepare_greet_sms(patient, patient_greet_status):
    from ..practice.services import send_notification
    to_send, title, send_message, patient_langauge = False, patient_greet_status, "", patient.language if patient.language else 'ENGLISH'

    if patient.birthday_sms_email:
        if patient_greet_status == "BIRTHDAY" or patient_greet_status == "ANNIVERSARY":
            send_message, to_send = CONST_WISH_SMS[patient_langauge][patient_greet_status], True

    if to_send:
        send_message = send_message.replace('{{PATIENT}}',
                                            patient.user.first_name) if "{{PATIENT}}" in send_message else None
        send_sms(patient.user.mobile, send_message, patient_greet_status)
        send_notification(patient.user, None, CONST_PATIENTS, title, send_message, patient_greet_status)
        return True
    return False


def prepare_patient_payment_sms(payment):
    from ..practice.services import send_notification
    try:
        payment_data = PatientPayment.objects.get(id=payment.id)
    except:
        return "Invalid Patient Payment"
    to_send, title, send_message, invoice_data, invoice_payment = False, 'Payment Recieved', None, '', 0
    # practice_language=''
    if payment_data and payment_data.practice and payment_data.practice.language:
        practice_language = payment_data.practice.language

    language = payment_data.patient.language if payment_data and payment_data.patient and payment_data.patient.language else practice_language
    communications = Communications.objects.filter(practice=payment_data.practice.id, sms_language=language,
                                                   is_active=True).values().order_by('-id').first()

    if communications and communications['payment_sms'] and communications['payment_text']:
        send_message, to_send = communications['payment_text'], True

    if to_send and send_message:
        serilaized_data = PatientPaymentSerializer(payment_data).data
        send_message = send_message.replace('{{PATIENT_ID}}', serilaized_data['patient_data']['custom_id'])
        send_message = send_message.replace('{{CLINICCONTACTNUMBER}}', communications['contact_number'])
        send_message = send_message.replace('{{CLINIC}}', communications['sms_clinic_name'])
        send_message = send_message.replace('{{PATIENT}}', serilaized_data['patient_data']['user']['first_name'])
        send_message = send_message.replace('{{DATE}}',
                                            (datetime.strptime(serilaized_data['date'], '%Y-%m-%d').date()).strftime(
                                                '%d %B, %Y'))
        send_message = send_message.replace('{{PAYMENT_ID}}', serilaized_data['payment_id'])
        for invoices in serilaized_data['invoices']:
            invoice_data = invoice_data + invoices['invoice_id'] + ', '
            invoice_payment = invoice_payment + invoices['pay_amount']
        send_message = send_message.replace('{{INVOICE_ID}}', re.sub(r', $', r'', invoice_data))
        send_message = send_message.replace('{{PAYMENT_AMOUNT}}', str(invoice_payment))
        send_message = send_message.replace('{{ADVANCE_AMOUNT}}', str(serilaized_data['advance_value']))
        send_sms(payment_data.patient.user.mobile, send_message, "PAYMENT SMS")
        send_notification(payment_data.patient.user, payment_data.practice.pk, CONST_PATIENTS, title, send_message,
                          "PAYMENT SMS")
    return
