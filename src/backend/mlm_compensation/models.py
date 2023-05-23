from django.db import models

# Create your models here.
from ..base.models import TimeStampedModel


class PointsToBusinessAdvisor(TimeStampedModel):
    point_value = models.FloatField(null=True, blank=True)
    business_value = models.FloatField(null=True, blank=True)
    return_days = models.IntegerField(null=True, blank=True)
    min_amount = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ProductMarginAdvisor(TimeStampedModel):
    name = models.CharField(max_length=524, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    level_count = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class RoleComissionAdvisor(TimeStampedModel):
    level = models.PositiveIntegerField(blank=True, null=True)
    margin = models.ForeignKey(ProductMarginAdvisor, blank=True, null=True, on_delete=models.PROTECT)
    commision_percent = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


