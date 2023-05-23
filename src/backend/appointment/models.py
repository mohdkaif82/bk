# Create your models here.
from ..base.models import TimeStampedModel
from ..practice.models import PracticeStaff, Practice, AppointmentCategory
from django.db import models

APPOINTMENT_STATUS_CHOICES = (
    ('Scheduled', 'SCHEDULED'),
    ('Waiting', 'WAITING'),
    ('Engaged', 'ENGAGED'),
    ('Check Out', 'CHECKOUT'),
    ('Cancelled', 'CANCELLED'),
    ('No Show', 'NO SHOW')
)


class Appointment(TimeStampedModel):
    from ..patients.models import Patients, PatientProcedure
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    notify_via_sms = models.BooleanField(default=True)
    notify_via_email = models.BooleanField(default=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    category = models.ForeignKey(AppointmentCategory, blank=True, null=True, on_delete=models.PROTECT)
    procedure = models.ForeignKey(PatientProcedure, blank=True, null=True, on_delete=models.PROTECT)
    notes = models.CharField(max_length=512, null=True, blank=True)
    cancel_by = models.CharField(max_length=512, null=True, blank=True)
    cancel_reason = models.CharField(max_length=512, null=True, blank=True)
    slot = models.PositiveSmallIntegerField(blank=True, null=True)
    schedule_at = models.DateTimeField(blank=True, null=True)
    schedule_till = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=64, choices=APPOINTMENT_STATUS_CHOICES, default='Scheduled')
    waiting = models.DateTimeField(blank=True, null=True)
    engaged = models.DateTimeField(blank=True, null=True)
    checkout = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return "%s" % (self.name)


class BlockCalendar(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    block_from = models.DateTimeField(blank=True, null=True)
    block_to = models.DateTimeField(blank=True, null=True)
    event = models.CharField(max_length=512, null=True, blank=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    allow_booking = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
