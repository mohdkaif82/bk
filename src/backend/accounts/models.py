# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from .managers import PasswordResetCodeManager, UserManager
from ..base.models import TimeStampedModel
from ..constants import ROLES_PERMISSIONS
from ..utils import short_data
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, \
    PermissionsMixin
# Sending Email
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    first_name = models.CharField(max_length=128, blank=True, null=True, default='')
    last_name = models.CharField(max_length=128, blank=True, null=True, default='')
    mobile = models.CharField(max_length=128, blank=True, null=True, default='', unique=True)
    email = models.EmailField(max_length=256, null=True, blank=True, default='')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    referer_code = models.CharField(max_length=1024, blank=True, null=True, default='')
    referer = models.ForeignKey('self', related_name='referer_user', null=True, blank=True, on_delete=models.PROTECT)
    objects = UserManager()
    # Email address to be used as the username
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    class Meta:
        verbose_name_plural = 'Users'

    def __str__(self):
        """Returns the email of the User when it is printed in the console"""
        return self.mobile

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name or short_data.get_first_name(self.email)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = self.first_name
        if self.last_name:
            full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name or ''

    def assgin_user_permissions(self, practice, roles_list):
        from ..practice.models import PracticeUserPermissions
        if not (practice and roles_list):
            return True
        for role in roles_list:
            try:
                permissions_list = ROLES_PERMISSIONS.get(role.description, None)
                if permissions_list:
                    for permission_dict in permissions_list:
                        codename = permission_dict.get('codename', None)
                        name = permission_dict.get('name', None)
                        if name and codename:
                            user_permission, flag = PracticeUserPermissions.objects.get_or_create(user=self,
                                                                                                  practice=practice,
                                                                                                  name=name,
                                                                                                  codename=codename)

            except Exception as e:
                print(e)
        return True


class Role(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=False)


class AbstractBaseCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="User_Abstract", on_delete=models.PROTECT)
    code = models.CharField(_('code'), max_length=524, primary_key=True)
    uid = models.CharField(max_length=40, default='uidrequired')
    timestamp = models.CharField(max_length=40, default='timestamprequired')
    signature = models.CharField(max_length=40, default='signaturerequired')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def send_email(self):
        subject = "Reset Your Password"
        text_content = """Reset your password by clicking on this link:
                      %s{{ uid }}/{{ timestamp }}/{{ signature }}/{{  code }}
        """ % settings.PASSWORD_RESET_URL

        # subject = render_to_string(subject_file).strip()
        from_email = settings.DEFAULT_EMAIL_FROM
        to = self.user.email
        # bcc_email = settings.DEFAULT_EMAIL_BCC

        # Make some context available
        ctxt = {
            'url': settings.PASSWORD_RESET_URL,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': self.code.decode(),
            'uid': self.uid,
            'timestamp': self.timestamp,
            'signature': self.signature

        }
        print(ctxt)
        # text_content = render_to_string(txt_file, ctxt)
        html_content = render_to_string('email/password_reset.html', ctxt)
        try:
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, 'text/html')
            msg.send()
            print("Email Sent succesfully")
        except Exception:
            logger.exception("Unable to send the mail.")

    def __unicode__(self):
        return "{0}, {1}, {2}, {3}".format(self.code, self.uid, self.timestamp, self.signature)


class PasswordResetCode(AbstractBaseCode):
    objects = PasswordResetCodeManager()

    def send_password_reset_email(self):
        self.send_email()


class SMS_Records(TimeStampedModel):
    mobile = models.CharField(max_length=15, null=True, blank=True)
    body = models.CharField(max_length=1000, null=True, blank=True)
    request_id = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    sms_type = models.CharField(max_length=100, default='APPOINTMENT')
    user = models.ForeignKey(User, related_name='user_SMS_Record', on_delete=models.PROTECT, null=True, blank=True)


class PatientLogin(TimeStampedModel):
    phone_no = models.CharField(max_length=15, null=True)
    otp = models.CharField(max_length=15, blank=True, null=True)
    # maximum attempts user can make is 15, change the OTP when counter meets zero
    counter = models.IntegerField(blank=True, default=25)
    is_active = models.BooleanField(default=True)
    resend_counter = models.IntegerField(blank=True, default=25)


class StaffLogin(TimeStampedModel):
    phone_no = models.CharField(max_length=15, null=True)
    otp = models.CharField(max_length=15, blank=True, null=True)
    # maximum attempts user can make is 15, change the OTP when counter meets zero
    counter = models.IntegerField(blank=True, default=25)
    is_active = models.BooleanField(default=True)
    resend_counter = models.IntegerField(blank=True, default=25)


class TaskLogin(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    login = models.CharField(max_length=1024, blank=True, null=True)
    password = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class UserFcm(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    user_token = models.CharField(max_length=1024, blank=True, null=True)
    application = models.CharField(max_length=1024, blank=True, null=True)
    device = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
