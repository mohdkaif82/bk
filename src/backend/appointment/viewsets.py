# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import calendar
import time
from datetime import timedelta, datetime

import pandas as pd
from ..accounts.models import User
from .models import Appointment, BlockCalendar
from .permissions import AppointmentPermissions
from .serializers import AppointmentSerializer, BlockCalendarSerializer, AppointmentDataSerializer
from .services import update_block_calendar
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..billing.serializers import PatientInvoicesDataSerializer
from ..constants import CONST_CANCELLED, CONST_GLOBAL_PRACTICE
from ..patients.models import Patients, PatientMedicalHistory, PatientGroups, PatientProcedure, PatientInvoices, \
    PatientNotes, PersonalDoctorsPractice
from ..patients.serializers import PatientProcedureSerializer
from ..patients.services import update_patient_procedure
from ..practice.models import PracticeCalenderSettings, VisitingTime, Practice
from ..practice.services import dict_to_mail
from ..utils import timezone
from ..utils.email import appointment_email
from ..utils.followup import set_patient_follow_up
from ..utils.sms import prepare_appointment_sms
from django.db.models import Count, F
from django.db.models.functions import TruncMonth as Month, TruncYear as Year, TruncDay as Day
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class AppointmentViewSet(ModelViewSet):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    permission_classes = (AppointmentPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        clinic_id = self.request.query_params.get('id', None)
        patient_id = self.request.query_params.get('patient', None)
        doctor = self.request.query_params.get('doctor', None)
        status = self.request.query_params.get('status', None)
        sort_on = self.request.query_params.get('sort_on', None)
        pagination = self.request.query_params.get('pagination', False)
        queryset = super(AppointmentViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.serializer_class = AppointmentDataSerializer
        if pagination == "true":
            self.pagination_class = StandardResultsSetPagination
        if clinic_id:
            queryset = queryset.filter(practice__id=clinic_id)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if start:
            start = timezone.get_day_start(timezone.from_str(start))
            queryset = queryset.filter(schedule_at__gte=start)
        if end:
            end = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(schedule_at__lte=end)
        if category:
            queryset = queryset.filter(category=category)
        if doctor:
            queryset = queryset.filter(doctor=doctor)
        if status:
            queryset = queryset.filter(status=status)
        if start_time:
            queryset = queryset.filter(schedule_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(schedule_at__lte=end_time)
        if sort_on:
            queryset = queryset.order_by(sort_on)
        else:
            queryset = queryset.order_by('-schedule_at')
        return queryset

    # def create(self, request, *args, **kwargs):
    #     print(request.data)
    #     ser=AppointmentSerializer(data=request.data)
    #     if ser.is_valid():
    #         ser.save()
    #         print('posting')
    #     else:
    #         print('error is here',ser.errors)
        
    
    def update(self, request, *args, **kwargs):
        data = request.data
        queryset = super(AppointmentViewSet, self).get_queryset()
        queryset = queryset.filter(pk=kwargs.get('pk'))
        treatment_plans = data.pop("treatment_plans", [])
        procedure_id = queryset[0].procedure.pk if queryset[0].procedure else None
        send_update = False
        if "waiting" in data and data["waiting"] != queryset[0].waiting:
            data["waiting"] = datetime.now()
            try:
                set_patient_follow_up(queryset[0].patient.id, queryset[0].practice)
            except:
                print("Failed to set follow up")
        if "engaged" in data and data["engaged"] != queryset[0].engaged:
            data["engaged"] = datetime.now()
        if "checkout" in data and data["checkout"] != queryset[0].checkout:
            data["checkout"] = datetime.now()
        if "schedule_at" in data:
            schedule = pd.to_datetime(data["schedule_at"])
            if queryset[0].schedule_at.date() != schedule.date() or queryset[0].schedule_at.time() != schedule.time() or \
                    queryset[0].practice.id != data['practice']:
                send_update = True
        if 'patient' in data:
            patient_data = data.pop('patient')
            if patient_data.get('id', None):
                try:
                    patient = Patients.objects.get(id=patient_data.get('id'))
                    patient = Patients.objects.filter(id=patient_data.get('id')).values('id').first()
                except:
                    return response.BadRequest({"detail": "No such patient exists"})
            else:
                medical_history = patient_data.pop('medical_history') if 'medical_history' in patient_data else []
                patient_group = patient_data.pop('patient_group') if 'patient_group' in patient_data else []
                practices = patient_data.pop('practices') if 'practices' in patient_data else []
                user = patient_data.pop('user')
                user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
                if not user_data:
                    user_data = User.objects.create(mobile=user['mobile'], email=user['email'],
                                                    first_name=user['first_name'], is_active=True)
                    if 'referer_code' in user and user['referer_code'] and User.objects.filter(
                            referer_code=user['referer_code']).exists():
                        user_data.referer = User.objects.filter(referer_code=data['referer_code'])[0]
                    user_data.save()
                    user_data = User.objects.filter(mobile=user['mobile']).values('id').first()
                patient = Patients.objects.filter(user__id=user_data['id']).values('id').first()
                if not patient:
                    patient = Patients.objects.create(**patient_data)
                    if patient.custom_id is None:
                        patient.custom_id = "BK" + str(patient.pk)
                    patient.user = User.objects.get(id=user_data['id'])
                    patient.medical_history.set(PatientMedicalHistory.objects.filter(id__in=medical_history))
                    patient.patient_group.set(PatientGroups.objects.filter(id__in=patient_group))
                    pdp = []
                    new_practices = []
                    for i in range(len(practices)):
                        for j in range(i + 1, len(practices)):
                            if practices[i]["practice"] == practices[j]["practice"]:
                                break
                        else:
                            new_practices.append(practices[i])
                    for practice_data in new_practices:
                        pdp.append(PersonalDoctorsPractice.objects.create(**practice_data))
                    patient.practices.set(pdp)
                    patient.save()
                    patient = Patients.objects.filter(user__id=user_data['id']).values('id').first()
            data['patient'] = Patients.objects.get(id=patient['id'])
        if len(treatment_plans):
            class x:
                data = {}

            x.data = {
                "id": procedure_id,
                'practice': data.get("practice", None),
                'patient': patient['id'],
                'doctor': data.get("doctor", None),
                'is_active': True,
                'treatment_plans': treatment_plans,
                'date': pd.to_datetime(data["schedule_at"]).date()
            }
            update_response = update_patient_procedure(x, PatientProcedureSerializer,
                                                       Patients.objects.get(id=patient['id']), PatientProcedure)
        else:
            data["procedure"] = None
        if "schedule_at" in data and data["schedule_at"] and "slot" in data and data["slot"]:
            data["schedule_till"] = pd.to_datetime(data["schedule_at"]) + timedelta(minutes=data["slot"])
        queryset.update(**data)
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.get_serializer(instance)
        if "status" in data:
            if data["status"] == CONST_CANCELLED:
                prepare_appointment_sms(instance, "CANCEL")
                appointment_email(instance, "CANCEL")
            if send_update and data["status"] != CONST_CANCELLED:
                prepare_appointment_sms(instance, "UPDATE")
        if "is_active" in data and data["is_active"] == False:
            prepare_appointment_sms(instance, "CANCEL")
            appointment_email(instance, "CANCEL")
        set_patient_follow_up(serializer.data["patient"]["id"], serializer.data["practice"])
        return response.Ok(serializer.data)

    @action(methods=['GET', 'POST'], detail=False)
    def block_calendar(self, request, *args, **kwargs):
        if request.method == 'GET':
            cal_fdate = request.query_params.get("cal_fdate", None)
            cal_tdate = request.query_params.get("cal_tdate", None)
            fdate = request.query_params.get("fdate", None)
            tdate = request.query_params.get("tdate", None)
            doctor = request.query_params.get("doctor", None)
            practice = request.query_params.get("practice", None)
            allow_booking = request.query_params.get("allow_booking", None)
            data = BlockCalendar.objects.filter(is_active=True, practice=practice)
            if allow_booking:
                allow_booking = True if allow_booking == 'true' else False
                data = data.filter(allow_booking=allow_booking)
            if cal_fdate and cal_tdate:
                data = data.filter(block_from__lte=cal_tdate, block_to__gte=cal_fdate)
            if doctor == "null":
                data = data.filter(doctor=None)
            elif doctor:
                data = data.filter(doctor=doctor) | data.filter(doctor=None)
            if fdate and tdate:
                data = data.filter(block_from__lt=tdate, block_to__gt=fdate)
            return response.Ok(BlockCalendarSerializer(data, many=True).data)
        else:
            if 'block_from' in request.data and 'block_to' in request.data and request.data['block_from'] >= \
                    request.data['block_to']:
                return response.BadRequest({"detail": "Block Start Time should be less than End Time"})
            update_response = update_block_calendar(request)
            if 'block_from' in request.data and 'block_to' in request.data:
                appointment_data = Appointment.objects.filter(schedule_at__gte=update_response['block_from'],
                                                              schedule_at__lte=update_response['block_to'],
                                                              practice=request.data["practice"]).exclude(
                    status=CONST_CANCELLED)
                if 'doctor' in request.data and request.data['doctor']:
                    appointment_data = appointment_data.filter(doctor=request.data['doctor'])
                for appointment in appointment_data:
                    prepare_appointment_sms(appointment, "CANCEL")
                appointment_data.update(status=CONST_CANCELLED)
                appointments = Appointment.objects.filter(schedule_at__gte=update_response['block_from'],
                                                          schedule_at__lte=update_response['block_to'],
                                                          practice=request.data["practice"])
                if 'doctor' in request.data and request.data['doctor']:
                    appointments = appointments.filter(doctor=request.data['doctor'])
                for appointment in appointments:
                    if appointment.patient and appointment.practice:
                        set_patient_follow_up(appointment.patient.pk, appointment.practice.pk)
            return response.Ok(update_response)

    @action(methods=['GET', 'POST'], detail=False)
    def appointment_report(self, request, *args, **kwargs):
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        doctors = request.query_params.get('doctors', None)
        categories = request.query_params.get('categories', None)
        practice = request.query_params.get('practice', None)
        report_type = request.query_params.get('type', None)
        cancelled = request.query_params.get('exclude_cancelled', None)
        first_app = request.query_params.get('first', None)
        converted = request.query_params.get('converted', None)
        mail_to = request.query_params.get('mail_to', None)
        city = request.query_params.get('city', None)
        state = request.query_params.get('state', None)
        country = request.query_params.get('country', None)
        cancelled = True if cancelled == "true" else False if cancelled else None
        first_app = True if first_app == "true" else False if first_app else None
        converted = True if converted == "true" else False if converted else None
        practice_name = CONST_GLOBAL_PRACTICE
        queryset = Appointment.objects.filter(is_active=True)
        if cancelled:
            queryset = queryset.exclude(status=CONST_CANCELLED)
        if start and end:
            start_date = timezone.get_day_start(pd.to_datetime(start))
            end_date = timezone.get_day_end(pd.to_datetime(end))
            queryset = queryset.filter(schedule_at__range=[start_date, end_date])
        if practice:
            queryset = queryset.filter(practice=practice)
            instance = Practice.objects.filter(id=practice).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(doctor__in=doctor_list)
        if city:
            queryset = queryset.filter(patient__city=city)
        if state:
            queryset = queryset.filter(patient__state=state)
        if country:
            queryset = queryset.filter(patient__country=country)
        if categories:
            category_list = categories.split(",")
            queryset = queryset.filter(category__in=category_list)
        if report_type == "CATEGORY":
            no_category = queryset.filter(category=None).count()
            result = list(
                queryset.exclude(category=None).values('category__name').annotate(count=Count("category__name"),
                                                                                  category=F('category__name')).values(
                    'count', 'category').order_by("-count"))
            if no_category > 0:
                result.append({"category": "No Category Assigned", "count": no_category})
            if mail_to:
                ready_data = []
                for item in result:
                    ready_data.append({"Category": item["category"], "Count": item["count"]})
                subject = "Category Wise Appointment Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Category_Wise_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "CANCEL_NUMBERS":
            no_reason = queryset.filter(status=CONST_CANCELLED, cancel_by=None).count()
            scheduled_count = queryset.exclude(status=CONST_CANCELLED).count()
            cancel_count = queryset.filter(status=CONST_CANCELLED).exclude(cancel_by=None).annotate(
                count=Count('cancel_by'), type=F('cancel_by')).values('count', 'type')
            result = [{"type": "Scheduled", "count": scheduled_count}] + list(cancel_count) + [
                {"type": "No reason", "count": no_reason}]
            if mail_to:
                subject = "Cancellation Numbers Appointment Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Cancellation Numbers report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(result, "Cancel_No_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "CANCELLATION":
            cancel_data = queryset.filter(status=CONST_CANCELLED)
            result = AppointmentDataSerializer(cancel_data, many=True).data
            if mail_to:
                ready_data = []
                for data in result:
                    ready_data.append({
                        "Date": pd.to_datetime(data['schedule_at']).strftime("%d/%m/%Y %H:%M:%S") if data[
                            'schedule_at'] else "--",
                        "Patient Id": data['patient']['custom_id'],
                        "Patient Name": data['patient']['user']['first_name'],
                        "Appointment Status": data['status'],
                        "Doctor Name": data['doctor_data']['user']['first_name'] if data['doctor_data'] else "--",
                        "Appointment Category": data['category_data'] if data['category_data'] else "--"
                    })
                subject = "Cancellation Appointment data Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Cancellation data report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Cancel_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DAILY":
            total = queryset.count()
            queryset = queryset.annotate(year=Year('schedule_at'), month=Month('schedule_at'),
                                         day=Day('schedule_at')).values('year', 'month', 'day').annotate(
                count=Count('id')).order_by('-year', '-month', '-day')
            for res in queryset:
                res['day'] = res['day'].strftime('%d')
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime(int(res['year']), int(res['month']), int(res['day'])).date()
            result = {"data": queryset, "total": total}
            if mail_to:
                ready_data = []
                for item in queryset:
                    ready_data.append(
                        {"Day": pd.to_datetime(item["date"]).strftime("%d/%m/%Y"), "Count": item["count"]})
                subject = "Daily Appointment Summary Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Daily Appointment Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "MONTHLY":
            total = queryset.count()
            queryset = queryset.annotate(year=Year('schedule_at'), month=Month('schedule_at')).values('year',
                                                                                                      'month').annotate(
                count=Count('id')).order_by('-year', '-month')
            for res in queryset:
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime(int(res['year']), int(res['month']), 1).date()
            result = {"data": queryset, "total": total}
            if mail_to:
                ready_data = []
                for item in queryset:
                    ready_data.append(
                        {"Month": pd.to_datetime(item["date"]).strftime("%B %Y"), "Count": item["count"]})
                subject = "Monthly Appointment Summary Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Monthly Appointment Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DOCTOR":
            no_doctor = queryset.filter(doctor=None).count()
            result = list(
                queryset.exclude(doctor=None).values('doctor__user__first_name').annotate(
                    count=Count("doctor__user__first_name"), doctor=F('doctor__user__first_name')) \
                    .values('doctor', 'count').order_by("-count"))
            if no_doctor > 0:
                result.append({"doctor": "No Doctor Assigned", "count": no_doctor})
            if mail_to:
                ready_data = []
                for item in result:
                    ready_data.append(
                        {"Doctor": item["doctor"], "Count": item["count"]})
                subject = "Doctor Wise Appointment Summary Report for " + practice_name + " from " \
                          + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Doctor Wise Appointment Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Doctor_Wise_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "PATIENT_GROUPS":
            total = queryset.exclude(patient__patient_group=None).values('patient__patient_group__name').count()
            queryset = queryset.exclude(patient__patient_group=None).values('patient__patient_group__name').annotate(
                count=Count('patient__patient_group__name'), patient_group=F('patient__patient_group__name')).values(
                'patient_group', 'count').order_by("-count")
            result = {"data": queryset, "total": total}
            if mail_to:
                ready_data = []
                for item in queryset:
                    ready_data.append(
                        {"Patient Group": item["patient_group"], "Count": item["count"]})
                subject = "Patient Group Appointment Summary Report for " + practice_name + " from " \
                          + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Patient Group Appointment Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Group_Appointment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DAILY_WAIT":
            result = {}
            resp = []
            queryset = queryset.exclude(waiting=None).exclude(engaged=None).exclude(checkout=None)
            for appointment in queryset.order_by('-schedule_at'):
                date = str(appointment.schedule_at.date())
                if date in result:
                    data = result[date]
                else:
                    data = {"wait": 0.0, "engage": 0.0}
                data["wait"] += (appointment.engaged - appointment.waiting).total_seconds()
                data["engage"] += (appointment.checkout - appointment.engaged).total_seconds()
                result[date] = data
            for key in result.keys():
                data = result[key]
                data["date"] = key
                data["stay"] = data["wait"] + data["engage"]
                resp.append(data)
            if mail_to:
                ready_data = []
                for item in resp:
                    ready_data.append({
                        "Date": pd.to_datetime(item["date"]).strftime("%d/%m/%Y"),
                        "Wait": time.strftime('%H:%M:%S', time.gmtime(item["wait"])),
                        "Stay": time.strftime('%H:%M:%S', time.gmtime(item["stay"])),
                        "Engage": time.strftime('%H:%M:%S', time.gmtime(item["engage"]))
                    })
                subject = "Daily Waiting Time Summary Report for " + practice_name + " from " \
                          + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Daily Waiting Time Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Waiting_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                resp = {"detail": msg, "error": error}
            if "error" in resp and resp["error"]:
                return response.BadRequest(resp)
            return response.Ok(resp)
        elif report_type == "MONTHLY_WAIT":
            result = {}
            resp = []
            queryset = queryset.exclude(waiting=None).exclude(engaged=None).exclude(checkout=None)
            for appointment in queryset.order_by('-schedule_at'):
                date = str(appointment.schedule_at.strftime('%Y') + "-" + appointment.schedule_at.strftime('%m'))
                if date in result:
                    data = result[date]
                else:
                    data = {"wait": 0.0, "engage": 0.0}
                data["wait"] += (appointment.engaged - appointment.waiting).total_seconds()
                data["engage"] += (appointment.checkout - appointment.engaged).total_seconds()
                result[date] = data
            for key in result.keys():
                data = result[key]
                data["date"] = key + "-01"
                data["stay"] = data["wait"] + data["engage"]
                resp.append(data)
            if mail_to:
                ready_data = []
                for item in resp:
                    ready_data.append({
                        "Date": pd.to_datetime(item["date"]).strftime("%B %Y"),
                        "Wait": time.strftime('%H:%M:%S', time.gmtime(item["wait"])),
                        "Stay": time.strftime('%H:%M:%S', time.gmtime(item["stay"])),
                        "Engage": time.strftime('%H:%M:%S', time.gmtime(item["engage"]))
                    })
                subject = "Monthly Waiting Time Summary Report for " + practice_name + " from " \
                          + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Monthly Waiting Time Summary Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Waiting_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                resp = {"detail": msg, "error": error}
            if "error" in resp and resp["error"]:
                return response.BadRequest(resp)
            return response.Ok(resp)
        elif report_type == "CONVERSION_REPORT":
            patients = []
            data = []
            ready_data = []
            index = 0
            for appointment in queryset:
                count = Appointment.objects.exclude(status='Scheduled').filter(patient=appointment.patient,
                                                                               id__lt=appointment.id,
                                                                               is_active=True).count()
                first = True if count == 0 else False
                if first_app is not None:
                    if first != first_app:
                        continue
                date = appointment.schedule_at.date()
                start1 = pd.to_datetime(date).date()
                end1 = pd.to_datetime(date) + timedelta(days=0)
                invoice = PatientInvoices.objects.filter(date__range=[start1, end1], is_active=True,
                                                         patient=appointment.patient, is_cancelled=False)
                first_invoice = invoice.last()
                patient = appointment.patient
                inv_data = PatientInvoicesDataSerializer(first_invoice).data if first_invoice else None
                notes_data = PatientNotes.objects.filter(is_active=True, patient=appointment.patient,
                                                         modified_at__range=[timezone.get_day_start(start1),
                                                                             timezone.get_day_end(end1)]).last()
                if converted is not None:
                    if (converted and not inv_data) or (not converted and inv_data):
                        continue
                if mail_to:
                    index += 1
                    ready_data.append({
                        "S.No.": index,
                        "Date": pd.to_datetime(date).strftime("%d/%m/%Y"),
                        "Patient Id": patient.custom_id,
                        "Patient Name": patient.user.first_name,
                        "Gender": patient.gender,
                        "DOB": patient.dob,
                        "Contact Number": patient.user.mobile,
                        "Secondary Number": patient.secondary_mobile_no,
                        "Contact Email": patient.user.email,
                        "Address": patient.address,
                        "Source": patient.source.name if patient.source else "--",
                        "Appointment": appointment.schedule_at.strftime(
                            "%d/%m/%Y %H:%M:%S") if appointment.schedule_at else "--",
                        "Appointment Status": appointment.status,
                        "Doctor Name": appointment.doctor.user.first_name if appointment.doctor else "--",
                        "Last Note": notes_data.name if notes_data else "--",
                        "Note By": notes_data.staff.user.first_name if notes_data else "--",
                        "Last Payment": inv_data["payments_data"] if inv_data else "--",
                        "Referal By": patient.user.referer.first_name if patient.user and patient.user.referer else "--",
                        "First Appointment": "Yes" if first else "No",
                        "Patient Conversion": "Yes" if inv_data else "No",
                        "City": patient.city.name if patient.city else "--",
                        "State": patient.state.name if patient.state else "--",
                        "Country": patient.country.name if patient.country else "--"
                    })
                else:
                    data.append({
                        "date": date,
                        "patient_name": patient.user.first_name,
                        "mobile": patient.user.mobile,
                        "secondary_number": patient.secondary_mobile_no,
                        "email": patient.user.email,
                        "id": patient.id,
                        "custom_id": patient.custom_id,
                        "gender": patient.gender,
                        "dob": patient.dob,
                        "image": patient.image,
                        "source": patient.source.name if patient.source else None,
                        "address": patient.address,
                        "locality": patient.locality,
                        "city": patient.city.name if patient.city else None,
                        "state": patient.state.name if patient.state else None,
                        "country": patient.country.name if patient.country else None,
                        "invoice_total": first_invoice.total if first_invoice else None,
                        "invoice_data": first_invoice.date if first_invoice else None,
                        "payment_total": inv_data["payments_data"] if inv_data else None,
                        "invoice_id": inv_data["invoice_id"] if inv_data else None,
                        "last_note": notes_data.name if notes_data else None,
                        "doctor": appointment.doctor.user.first_name if appointment.doctor else None,
                        "note_by": notes_data.staff.user.first_name if notes_data else None,
                        "appointment": appointment.schedule_at,
                        "status": appointment.status,
                        "referal_by": patient.user.referer.first_name if patient.user and patient.user.referer else "--",
                        "first_appointment": first
                    })
                    patients.append(patient.id)
            distinct_patients = len(set(patients))
            resp = {"distinct_patients": distinct_patients, "data": data}
            if mail_to:
                subject = "Patient Conversion Report for " + practice_name + " from " \
                          + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Patient Conversion Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Conversion_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                resp = {"detail": msg, "error": error}
            if "error" in resp and resp["error"]:
                return response.BadRequest(resp)
            return response.Ok(resp)
        else:
            return response.BadRequest({"detail": "Invalid type sent"})

    @action(methods=['GET', 'POST'], detail=False)
    def availability(self, request, *args, **kwargs):
        start_time = request.query_params.get("startDate", None)
        slot = request.query_params.get("slot", None)
        doctor = request.query_params.get("doctor", None)
        practice = request.query_params.get("practice", None)
        if start_time and slot:
            start = pd.to_datetime(start_time)
            end = start + timedelta(minutes=int(slot))
            weekday = calendar.day_name[start.weekday()].lower()
        else:
            return response.BadRequest({"detail": "Please send startDate and slot with data"})
        output = {
            "practice_error": False,
            "doctor_error": False,
            "appointment_error": False,
            "block_error": False
        }
        if doctor and practice:
            timings = VisitingTime.objects.filter(practice=practice, doctor=doctor, is_active=True).first()
            if timings and timings.visting_hour_same_week:
                if timings.first_start_time > start.time() or timings.first_start_time > end.time() or timings.second_end_time < start.time() or timings.second_end_time < end.time():
                    output["doctor_error"] = True
                if timings.is_two_sessions and timings.first_end_time < start.time() < timings.second_start_time and timings.first_end_time < end.time() < timings.second_start_time:
                    output["doctor_error"] = True
            else:
                timings_dict = VisitingTime.objects.filter(practice=practice, doctor=doctor,
                                                           is_active=True).values().first()
                if timings_dict:
                    if timings_dict["first_start_time_" + weekday] > start.time() or timings_dict[
                        "first_start_time_" + weekday] > end.time() or timings_dict[
                        "second_end_time_" + weekday] < start.time() or timings_dict[
                        "second_end_time_" + weekday] < end.time():
                        output["doctor_error"] = True
                    if timings_dict["is_two_sessions_" + weekday] and timings_dict[
                        "first_end_time_" + weekday] < start.time() < timings_dict["second_start_time_" + weekday] and \
                            timings_dict["first_end_time_" + weekday] < end.time() < timings_dict[
                        "second_start_time_" + weekday]:
                        output["doctor_error"] = True
        if practice:
            timings = PracticeCalenderSettings.objects.filter(practice=practice, is_active=True).first()
            if timings and timings.visting_hour_same_week:
                if timings.first_start_time > start.time() or timings.first_start_time > end.time() or timings.second_end_time < start.time() or timings.second_end_time < end.time():
                    output["practice_error"] = True
                if timings.is_two_sessions and timings.first_end_time < start.time() < timings.second_start_time and timings.first_end_time < end.time() < timings.second_start_time:
                    output["practice_error"] = True
            else:
                timings_dict = PracticeCalenderSettings.objects.filter(practice=practice,
                                                                       is_active=True).values().first()
                if timings_dict:
                    if timings_dict["first_start_time_" + weekday] > start.time() or timings_dict[
                        "first_start_time_" + weekday] > end.time() or timings_dict[
                        "second_end_time_" + weekday] < start.time() or timings_dict[
                        "second_end_time_" + weekday] < end.time():
                        output["practice_error"] = True
                    if timings_dict["is_two_sessions_" + weekday] and timings_dict[
                        "first_end_time_" + weekday] < start.time() < timings_dict["second_start_time_" + weekday] and \
                            timings_dict["first_end_time_" + weekday] < end.time() < timings_dict[
                        "second_start_time_" + weekday]:
                        output["practice_error"] = True
            if Appointment.objects.exclude(status=CONST_CANCELLED).filter(schedule_at__lte=end,
                                                                          schedule_till__gte=start,
                                                                          is_active=True).exists():
                output["appointment_error"] = True
            block = BlockCalendar.objects.filter(block_from__lte=end, block_to__gte=start, is_active=True,
                                                 allow_booking=False)
            if doctor:
                block = block.filter(doctor=doctor)
            else:
                block = block.filter(doctor=None)
            if block.exists():
                output["block_error"] = True
            return response.Ok(output)
        else:
            return response.BadRequest({"detail": "Please select a Clinic"})
