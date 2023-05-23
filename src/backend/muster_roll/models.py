from ..base.models import TimeStampedModel
from ..practice.models import Practice
from django.contrib.auth import get_user_model
from django.db import models


class HrSettings(TimeStampedModel):
    practice = models.ForeignKey(Practice, null=True, blank=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    value = models.CharField(max_length=1024, blank=True, null=True)
    detail = models.CharField(max_length=1024, blank=True, null=True)
    color = models.CharField(max_length=1024, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)


class UserTasks(TimeStampedModel):
    assignee = models.ForeignKey(get_user_model(), related_name="task_user", on_delete=models.PROTECT)
    reporter = models.ForeignKey(get_user_model(), related_name="task_reporter", on_delete=models.PROTECT)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(get_user_model(), null=True, blank=True, related_name="task_completed",
                                     on_delete=models.PROTECT)
    complete_remark = models.CharField(max_length=1024, blank=True, null=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    remark = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    priority = models.ForeignKey(HrSettings, null=True, blank=True, on_delete=models.PROTECT)
    is_recurring = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class TaskTemplates(TimeStampedModel):
    department = models.ForeignKey(HrSettings, related_name="task_department", on_delete=models.PROTECT)
    designation = models.ForeignKey(HrSettings, related_name="task_designation", on_delete=models.PROTECT)
    days = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    remark = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    priority = models.ForeignKey(HrSettings, null=True, blank=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class TaskComments(TimeStampedModel):
    task = models.ForeignKey(UserTasks, on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class TaskStatus(TimeStampedModel):
    task = models.ForeignKey(UserTasks, on_delete=models.PROTECT)
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ManagerRating(TimeStampedModel):
    user = models.ForeignKey(get_user_model(), related_name="rating_user", on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class TargetHeads(TimeStampedModel):
    department = models.ForeignKey(HrSettings, related_name="target_department", on_delete=models.PROTECT)
    designation = models.ForeignKey(HrSettings, related_name="target_designation", on_delete=models.PROTECT)
    project = models.ForeignKey(HrSettings, related_name="target_projects", on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class MonthlyTarget(TimeStampedModel):
    month = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    head = models.ForeignKey(TargetHeads, related_name="month_target_head", on_delete=models.PROTECT)
    target = models.IntegerField(blank=True, null=True)
    working_days = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class UserTarget(TimeStampedModel):
    date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(get_user_model(), related_name="user_target", on_delete=models.PROTECT, blank=True,
                             null=True)
    head = models.ForeignKey(TargetHeads, related_name="user_target_head", on_delete=models.PROTECT, blank=True,
                             null=True)
    target = models.IntegerField(blank=True, null=True)
    remarks = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
