from ..appointment.models import Appointment
from ..patients.models import Patients
from ..practice.models import Communications
from dateutil.relativedelta import relativedelta


def set_patient_follow_up(patient, practice):
    last_appointment = Appointment.objects.filter(patient=patient, is_active=True).exclude(status='Cancelled').order_by(
        '-schedule_at').first()
    communication = Communications.objects.filter(practice=practice, is_active=True).order_by('-modified_at').first()
    months = int(communication.send_follow_up_reminder_time) if communication.send_follow_up_reminder_time else 0
    if last_appointment and months > 0:
        followup_date = last_appointment.schedule_at.date() + relativedelta(months=months)
        Patients.objects.filter(id=patient).update(follow_up_date=followup_date)
    return
