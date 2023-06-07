from ..base.models import TimeStampedModel
from ..patients.models import Patients
from ..practice.models import PracticeStaff
from django.db import models

Call_STATUS_CHOICES = (
    ('Scheduled', 'SCHEDULED'),
    ('Waiting', 'WAITING'),
    ('ReScheduled', 'RESCHEDULED'),
    ('Cancelled', 'CANCELLED'),
)
Call_TYPE_CHOICES = (
    ('video', 'VIDEO'),
    ('audio', 'audio'),
)

class Meeting(TimeStampedModel):
    name = models.CharField(max_length=500, blank=True, null=True)
    agenda = models.CharField(max_length=1000, blank=True, null=True)
    participants = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    admins = models.ManyToManyField(PracticeStaff, blank=True, related_name="admin")
    doctors = models.ManyToManyField(PracticeStaff, blank=True, related_name="staff")
    meeting_type=models.CharField(max_length=50,default='offline')
    patients = models.ManyToManyField(Patients, blank=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    room_id = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class VideoCall(models.Model):
    call_duration = models.IntegerField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    doctors_call = models.ForeignKey(PracticeStaff,on_delete=models.CASCADE ,blank=True, related_name="call_for_staff")
    patients_call = models.ForeignKey(Patients,on_delete=models.CASCADE, null=True,blank=True,related_name='patients')
    call_id = models.CharField(max_length=100, blank=True, null=True)
    call_type = models.CharField(max_length=100, choices=Call_TYPE_CHOICES,blank=True, null=True)
    notify_via_email = models.BooleanField(default=True)
    cancel_by = models.CharField(max_length=512, null=True, blank=True)
    cancel_reason = models.CharField(max_length=512, null=True, blank=True)
    status = models.CharField(max_length=64, choices=Call_STATUS_CHOICES, default='Waiting')
    is_active = models.BooleanField(default=True)
    
    
class MeetingJoinee(TimeStampedModel):
    meeting = models.ForeignKey(Meeting, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT, related_name="staff_user")
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    is_allowed = models.BooleanField(default=True)
    allowed_by = models.ForeignKey(PracticeStaff, blank=True, null=True, related_name="allowed_by",
                                   on_delete=models.PROTECT)
    is_blocked = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)


class MeetingChat(TimeStampedModel):
    joinee = models.ForeignKey(MeetingJoinee, blank=True, null=True, on_delete=models.PROTECT)
    message = models.CharField(max_length=1024, blank=True, null=True)
    is_public = models.NullBooleanField(default=None, null=True)
    is_active = models.BooleanField(default=True)


class RoomMember(models.Model):
    name = models.CharField(max_length=200)
    uid = models.CharField(max_length=1000)
    room_name = models.CharField(max_length=200)
    insession = models.BooleanField(default=True)

    def __str__(self):
        return self.name