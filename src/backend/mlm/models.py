from django.db import models

# Create your models here.
from ..base.models import TimeStampedModel


class AgentRole(TimeStampedModel):
    name = models.CharField(max_length=128, null=True, blank=True)
    is_active = models.BooleanField(default=True)

class PointsToBusiness(TimeStampedModel):
    point_value = models.FloatField(null=True, blank=True)
    bussiness_value = models.FloatField(null=True, blank=True)
    return_days = models.IntegerField(null=True, blank=True)
    min_amount = models.BooleanField(default=True)


class ProductMargin(TimeStampedModel):
    name = models.CharField(max_length=524, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    level_count = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class RoleComission(TimeStampedModel):
    level = models.PositiveIntegerField(blank=True, null=True)
    role = models.ForeignKey(AgentRole, blank=True, null=True, on_delete=models.PROTECT)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    commision_percent = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


