from ..base.models import TimeStampedModel
from ..patients.models import Patients
from ..practice.models import PracticeStaff
from django.db import models


class Meeting(TimeStampedModel):
    name = models.CharField(max_length=500, blank=True, null=True)
    agenda = models.CharField(max_length=1000, blank=True, null=True)
    participants = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    admins = models.ManyToManyField(PracticeStaff, blank=True, related_name="admin")
    doctors = models.ManyToManyField(PracticeStaff, blank=True, related_name="staff")
    patients = models.ManyToManyField(Patients, blank=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
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
