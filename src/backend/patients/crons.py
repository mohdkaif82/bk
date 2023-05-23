from datetime import timedelta

from ..appointment.models import Appointment
from ..constants import CONST_APPOINTMENT_SUMMARY_SMS, CONST_APPOINTMENT_SUMMARY_STAFF_SMS, CONST_STAFF
from .models import Patients
from ..practice.models import PracticeStaff, PracticeStaffRelation
from ..practice.services import send_notification
from ..utils import timezone, sms, email
from django.db.models import Count


def follow_up_and_medicine_reminder():
    date_today = timezone.now_local(True)
    follow_up_reminder(date_today)
    medicine_reminder(date_today)
    return


def send_greetings():
    date_today = timezone.now_local(True)
    patient_anniversary(date_today)
    patient_birthday(date_today)
    return


def remind_appointment_today():
    date_today = timezone.now_local(True)
    appointment_reminder(date_today)
    return


def remind_appointment_tomorrow():
    date_today = timezone.now_local(True) + timedelta(days=1)
    appointment_reminder(date_today)
    return


def appointment_reminder(date):
    all_appointments = Appointment.objects.filter(schedule_at__date=date, is_active=True)
    for appointment in all_appointments:
        sms.prepare_appointment_sms(appointment, "REMINDER")
        email.appointment_email(appointment, "REMINDER")


def follow_up_reminder(date):
    all_patients = Patients.objects.filter(follow_up_date=date, follow_up_sms_email=True, is_active=True)
    for patient in all_patients:
        appointment = Appointment.objects.filter(patient=patient, is_active=True).last()
        sms.prepare_appointment_sms(appointment, "FOLLOWUP")
        email.appointment_email(appointment, "FOLLOWUP")


def medicine_reminder(date):
    all_patients = Patients.objects.filter(medicine_till=date, follow_up_sms_email=True, is_active=True)
    for patient in all_patients:
        appointment = Appointment.objects.filter(patient=patient, is_active=True).last()
        sms.prepare_appointment_sms(appointment, "MEDICINE")


def patient_anniversary(date):
    all_patients = Patients.objects.filter(anniversary__day=date.day, anniversary__month=date.month,
                                           birthday_sms_email=True, is_active=True)
    for patient in all_patients:
        sms.prepare_greet_sms(patient, "ANNIVERSARY")
        email.patient_greeting_email(patient, "ANNIVERSARY")


def patient_birthday(date):
    all_patients = Patients.objects.filter(dob__day=date.day, dob__month=date.month, birthday_sms_email=True,
                                           is_active=True)
    for patient in all_patients:
        sms.prepare_greet_sms(patient, "BIRTHDAY")
        email.patient_greeting_email(patient, "BIRTHDAY")


def appointment_summary():
    date_today = timezone.now_local(True)
    appointments = Appointment.objects.filter(schedule_at__date=date_today, is_active=True, doctor__schedule_sms=True)
    doctors = appointments.distinct('doctor').values(
        'doctor__user__mobile', 'doctor__user__first_name', 'doctor', 'doctor__user')
    for doctor in doctors:
        appointment_data = appointments.filter(doctor=doctor['doctor']).values('practice__name',
                                                                               'practice').order_by().annotate(
            practice_count=Count('practice__name'))
        sms_data = CONST_APPOINTMENT_SUMMARY_SMS.format(doctor['doctor__user__first_name'],
                                                        date_today.strftime("%d-%m-%Y"))
        for appointment in appointment_data:
            sms_data += appointment['practice__name'] + ": " + str(appointment['practice_count']) + "\n"
        sms.send_sms_without_save(doctor['doctor__user__mobile'], sms_data)
        title = "Today's Summary"
        send_notification(doctor['doctor__user'], appointment_data[0]['practice'], CONST_STAFF, title, sms_data,
                          "Calendar")

    all_staff = PracticeStaff.objects.filter(is_active=True, schedule_sms=True)
    appointment_dict = {}
    all_appointments = Appointment.objects.filter(schedule_at__date=date_today, is_active=True).values(
        'practice_id').order_by().annotate(practice_count=Count('practice_id'))
    for appointment in all_appointments:
        appointment_dict[appointment["practice_id"]] = appointment['practice_count']
    for staff in all_staff:
        send = False
        sms_data = CONST_APPOINTMENT_SUMMARY_STAFF_SMS.format(date_today.strftime("%d-%m-%Y"))
        all_perms = PracticeStaffRelation.objects.filter(staff=staff, is_active=True)
        notify_practice = all_perms.first().practice.pk if all_perms.first() else None
        for perm in all_perms:
            practice = perm.practice.pk
            if practice in appointment_dict:
                send = True
                sms_data += perm.practice.name + ": " + str(appointment_dict[practice]) + "\n"
        if send and staff.user and staff.user.mobile:
            sms.send_sms_without_save(staff.user.mobile, sms_data)
            title = "Today's Summary"
            send_notification(staff.user, notify_practice, CONST_STAFF, title, sms_data, "Calendar")
    return 