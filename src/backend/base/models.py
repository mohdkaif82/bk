# from django.contrib.gis.db import models as geomodels
from ..utils import timezone
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_('created'), auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(_('modified'), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        abstract = True


def upload_clinic_image(instance, image):
    """
    Stores the attachment in a "per rb-gallery/module-type/yyyy/mm/dd" folder.
    :param instance, filename
    :returns ex: oct-gallery/User-profile/2016/03/30/filename
    """
    today = timezone.get_today_start()
    return 'clinic-image/{model}/{year}/{month}/{day}/{image}'.format(
        model=instance._meta.model_name,
        year=today.year, month=today.month,
        day=today.day, image=image,
    ).replace('+',' ')


def upload_blog_image(instance, image):
    """
    Stores the attachment in a "per rb-gallery/module-type/yyyy/mm/dd" folder.
    :param instance, filename
    :returns ex: oct-gallery/User-profile/2016/03/30/filename
    """
    today = timezone.get_today_start()
    now = timezone.now_local()
    return 'clinic-image/{model}/{year}/{month}/{day}/{time}/{image}'.format(
        model=instance._meta.model_name,
        year=today.year, month=today.month,
        day=today.day, time=now, image=image,
    ).replace('+',' ')


def upload_patient_image(instance, image):
    """
    Stores the attachment in a "per rb-gallery/module-type/yyyy/mm/dd" folder.
    :param instance, filename
    :returns ex: oct-gallery/User-profile/2016/03/30/filename
    """
    today = timezone.get_today_start()
    return 'patient-image/{model}/{year}/{month}/{day}/{image}'.format(
        model=instance._meta.model_name,
        year=today.year, month=today.month,
        day=today.day, image=image,
    ).replace('+',' ')
