import json
import os
import time
from csv import DictWriter
from datetime import datetime

import pandas as pd
import requests
from ..accounts.models import User
from ..appointment.models import Appointment
from ..appointment.serializers import AppointmentSerializer
from ..constants import CONST_CANCELLED, CONST_REPORT_MAIL
from ..constants import CONST_GLOBAL_PRACTICE
from ..patients.models import Reservations, PatientTreatmentPlans
from .models import PrescriptionTemplate, DrugCatalogTemplate, BedBookingPackage, PracticeStaff, \
    PracticeUserPermissions, PushNotifications, Practice
from .serializers import PrescriptionTemplateSerializer, DrugCatalogTemplateSerializer
from ..utils import timezone, email
from django.conf import settings
from django.db.models import F, Count
from django.db.models.functions import TruncMonth as Month, TruncYear as Year, TruncDay as Day


def seat_availability(practice, start, end, bed_package):
    try:
        package = BedBookingPackage.objects.get(id=bed_package)
    except:
        return {"detail": "Invalid Package"}
    normal_seats = package.room.normal_seats if package.room and package.room.normal_seats else 0
    tatkal_seats = package.room.tatkal_seats if package.room and package.room.tatkal_seats else 0
    if normal_seats == 0 and tatkal_seats == 0:
        return {"detail": "No Such Room exists on this clinic"}
    date_diff = pd.to_datetime(end) - pd.to_datetime(start)
    if date_diff.days + 1 != package.no_of_days:
        return {"detail": "Invalid time period selected"}
    normal = query_seats(practice.pk, normal_seats, "NORMAL", start, end, package.room.pk)
    tatkal = query_seats(practice.pk, tatkal_seats, "TATKAL", start, end, package.room.pk)
    return {"NORMAL": normal, "TATKAL": tatkal}


def query_seats(practice, seats, seat_type, start, end, room):
    available = False
    available_seat = -1
    for seat_no in range(1, seats + 1):
        queryset = Reservations.objects.filter(practice=practice, bed_package__room=room, seat_type=seat_type,
                                               seat_no=seat_no,
                                               payment_status="SUCCESSFUL")
        queryset = queryset.filter(from_date__lte=start, to_date__gte=end) \
                   | queryset.filter(from_date__gte=start, to_date__lte=end) \
                   | queryset.filter(from_date__lte=start, to_date__gte=start).filter(from_date__lte=end,
                                                                                      to_date__lte=end) \
                   | queryset.filter(from_date__gte=start, to_date__gte=start).filter(from_date__lte=end,
                                                                                      to_date__gte=end)
        total_bookings = queryset.count()
        if total_bookings == 0:
            available_seat = seat_no
            available = True
            break
    return {'available': available, "seat_no": available_seat}


def update_pratice_related_object(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy()
    new_data_request['practice'] = instance.pk
    filetags_id = new_data_request.pop('id', None)
    if filetags_id:
        filetags_object = model_class.objects.get(id=filetags_id)
        is_delete = new_data_request.pop('is_delete', None)
        if is_delete:
            filetags_object.delete()
            return {'detail': 'Object Deleted Successfully'}
        serializer = serializer_class(instance=filetags_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return (serializer_class(instance=update_object).data)
    else:
        serializer = serializer_class(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return (serializer_class(instance=update_object).data)


def update_pratice_related_drug_object(request, serializer_class, instance, model_class):
    from .models import DrugType, DrugUnit
    new_data_request = request.data.copy()
    new_data_request['practice'] = instance.pk
    filetags_id = new_data_request.pop('id', None)
    if filetags_id:
        filetags_object = model_class.objects.get(id=filetags_id)
        is_delete = new_data_request.pop('is_delete', None)
        if is_delete:
            filetags_object.delete()
            return {'detail': 'Object Deleted Successfully'}
        serializer = serializer_class(instance=filetags_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return (serializer_class(instance=update_object).data)
    else:
        serializer = serializer_class(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        extra_type = new_data_request.pop('drug_type_extra', None)
        unit_tpye_extra = new_data_request.pop('unit_type_extra', None)
        if extra_type:
            drug_type_obj, flag = DrugType.objects.get_or_create(practice=instance, name=extra_type)
            update_object.drug_type = drug_type_obj
            update_object.save()
        if unit_tpye_extra:
            unit_type_obj, flag = DrugUnit.objects.get_or_create(practice=instance, name=unit_tpye_extra)
            update_object.unit = unit_type_obj
            update_object.save()
        return (serializer_class(instance=update_object).data)


def get_emr_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    doctors = request.query_params.get("doctors", None)
    is_complete = request.query_params.get("is_complete", None)
    report_type = request.query_params.get("type", None)
    queryset = PatientTreatmentPlans.objects.filter(patientprocedure__practice=instance)
    mail_to = request.query_params.get('mail_to', None)
    practice_name = CONST_GLOBAL_PRACTICE
    ready_data = []
    if start_date and end_date:
        queryset = queryset.filter(patientprocedure__date__range=[start_date, end_date])
    if doctors:
        doctor_list = doctors.split(",")
        queryset = queryset.filter(patientprocedure__doctor__in=doctor_list)
    if is_complete:
        is_complete = True if is_complete == "true" else False
        if is_complete:
            queryset = queryset.filter(is_completed=is_complete)
    queryset = queryset.order_by("patientprocedure__date")
    if report_type == "ALL":
        queryset = queryset.annotate(date=F("patientprocedure__date"), procedure_name=F("procedure__name"),
                                     doctor=F("patientprocedure__doctor__user__first_name")) \
            .values("date", "doctor", "procedure_name", "quantity")
        if mail_to:
            for index, item in enumerate(queryset):
                ready_data.append({
                    "S. No.": index + 1,
                    "Performed On": item['date'].strftime("%d/%m/%Y") if item['date'] else "--",
                    "Name": item['procedure_name'],
                    "Performed by": item['doctor'],
                    "Total Treatments": item['quantity']
                })
            subject = "All Treatment For " + practice_name + " from " + start_date + " to " + end_date
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "All_Treatment__Report_" + start_date + "_" + end_date, mail_to,
                                      subject, body)
            queryset = {"detail": msg, "error": error}
            # return queryset
        return queryset
    elif report_type == "DAILY":
        total = queryset.count()
        queryset = queryset.annotate(year=Year('patientprocedure__date'), month=Month('patientprocedure__date'),
                                     day=Day('patientprocedure__date')).values('year', 'month', 'day').annotate(
            count=Count('id')).order_by('-year', '-month', '-day')
        for res in queryset:
            res['day'] = res['day'].strftime('%d')
            res['month'] = res['month'].strftime('%m')
            res['year'] = res['year'].strftime('%Y')
            res['date'] = datetime(int(res['year']), int(res['month']), int(res['day'])).date()
        if mail_to:
            for index, item in enumerate(queryset):
                ready_data.append({
                    "S. No.": index + 1,
                    "Day": item['date'].strftime("%d/%m/%Y") if item['date'] else "--",
                    "Total Treatments": item['count']
                })
            subject = "Daily Treatment Count Report for " + practice_name + " from " + start_date + " to " + end_date
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Daily_Treatment_count_Report_" + start_date + "_" + end_date,
                                      mail_to,
                                      subject, body)
            queryset = {"detail": msg, "error": error}
            return queryset
        return {"data": queryset, "total": total}
    elif report_type == "MONTHLY":
        total = queryset.count()
        queryset = queryset.annotate(year=Year('patientprocedure__date'), month=Month('patientprocedure__date')).values(
            'year', 'month').annotate(count=Count('id')).order_by('-year', '-month')
        for res in queryset:
            res['month'] = res['month'].strftime('%m')
            res['year'] = res['year'].strftime('%Y')
            res['date'] = datetime(int(res['year']), int(res['month']), 1).date()
        if mail_to:
            for index, item in enumerate(queryset):
                ready_data.append({
                    "S. No.": index + 1,
                    "Month": item['date'].strftime("%B %Y") if item['date'] else "--",
                    "Total Treatments": item['count']
                })
            subject = "Monthly Treatment Count Report for " + practice_name + " from " + start_date + " to " + end_date
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Monthly_Treatment_count_Report_" + start_date + "_" + end_date,
                                      mail_to,
                                      subject, body)
            queryset = {"detail": msg, "error": error}
            return queryset
        return {"data": queryset, "total": total}
    elif report_type == "DOCTOR":
        no_doctor = queryset.filter(patientprocedure__doctor=None).count()
        result = list(
            queryset.exclude(patientprocedure__doctor=None).values(
                'patientprocedure__doctor__user__first_name').annotate(
                count=Count("patientprocedure__doctor__user__first_name"),
                doctor=F('patientprocedure__doctor__user__first_name')).values('doctor', 'count').order_by("-count"))
        if no_doctor > 0:
            result.append({"doctor": "No Doctor Assigned", "count": no_doctor})

        if mail_to:
            for index, item in enumerate(result):
                ready_data.append({
                    "S. No.": index + 1,
                    "Doctor": item['doctor'],
                    "Total Treatments": item['count']
                })
            subject = "Treatment Each Doctor For " + practice_name + " from " + start_date + " to " + end_date
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Treatment_Each_Doctor_Report_" + start_date + "_" + end_date,
                                      mail_to,
                                      subject, body)
            result = {"detail": msg, "error": error}
        return result
    elif report_type == "CATEGORY":
        queryset = queryset.values("procedure__name").annotate(count=Count("procedure__name"),
                                                               procedure_name=F("procedure__name")).values(
            "procedure_name", "count").order_by("-count")

        if mail_to:
            for index, item in enumerate(queryset):
                ready_data.append({
                    "S. No.": index + 1,
                    "Treatment Category": item['procedure_name'],
                    "Total Treatments": item['count']
                })
            subject = "Treatment Each Category For " + practice_name + " from " + start_date + " to " + end_date
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Treatment_Each_Category_Report_" + start_date + "_" + end_date,
                                      mail_to,
                                      subject, body)
            queryset = {"detail": msg, "error": error}
        return queryset
    else:
        return {"error": True, "detail": "Invaild type sent"}


def get_appoinment_report(instance, request):
    start = request.query_params.get('start', None)
    end = request.query_params.get('end', None)
    patient = request.query_params.get('patient', None)
    doctors = request.query_params.get("doctors", None)
    categories = request.query_params.get("categories", None)
    exclude_cancelled = request.query_params.get("exclude_cancelled", None)
    with_deleted = request.query_params.get('with_deleted', "false")
    mail_to = request.query_params.get('mail_to', None)
    appointments = Appointment.objects.filter(practice=instance)
    if patient:
        appointments = appointments.filter(patient__id=patient)
    if exclude_cancelled:
        exclude_cancelled = True if exclude_cancelled == "true" else False
        if exclude_cancelled:
            appointments = appointments.exclude(status=CONST_CANCELLED)
    if doctors:
        doctor_list = doctors.split(",")
        appointments = appointments.filter(doctor__id__in=doctor_list)
    if categories:
        category_list = categories.split(",")
        appointments = appointments.filter(category__id__in=category_list)
    if start and end:
        start_date = timezone.get_day_start(pd.to_datetime(start))
        end_date = timezone.get_day_end(pd.to_datetime(end))
        appointments = appointments.filter(schedule_at__range=[start_date, end_date])
    if with_deleted:
        with_deleted = False if with_deleted == "false" else True
        appointments = appointments.exclude(is_active=with_deleted)
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        appointments = appointments.filter(order_by=sort_by)
    else:
        appointments.order_by('-schedule_at')
    if mail_to:
        subject = "Appointment Report for " + instance.name + " from " + start_date.strftime(
            "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
        body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
               + "<br/><b>" + instance.name + "</b>"
        ready_data = []
        for index, appointment in enumerate(AppointmentSerializer(appointments, many=True).data):
            schedule_date = timezone.localtime(
                pd.to_datetime(appointment["schedule_at"])).date() if appointment.get("schedule_at", None) else "--"
            schedule_time = timezone.localtime(
                pd.to_datetime(appointment["schedule_at"])).time() if appointment.get("schedule_at", None) else "--"
            checked_in = timezone.localtime(pd.to_datetime(appointment["waiting"])).strftime("%d/%m/%Y %H:%M:%S") \
                if appointment.get("waiting", None) else "--"
            engaged = timezone.localtime(pd.to_datetime(appointment["engaged"])).strftime("%d/%m/%Y %H:%M:%S") \
                if appointment.get("engaged", None) else "--"
            waited = time.strftime('%H:%M:%S', time.gmtime((pd.to_datetime(appointment["engaged"]) - pd.to_datetime(
                appointment["waiting"])).total_seconds())) if appointment.get("engaged", None) and \
                                                              appointment.get("waiting", None) else "--"
            checked_out = timezone.localtime(pd.to_datetime(appointment["checkout"])).strftime("%d/%m/%Y %H:%M:%S") \
                if appointment.get("checkout", None) else "--"
            patient_name = appointment["patient"]["user"]["first_name"] if appointment.get("patient", None) and \
                                                                           appointment.get("patient").get("user",
                                                                                                          None) and \
                                                                           appointment.get("patient").get("user").get(
                                                                               "first_name", None) else "--"
            patient_id = appointment["patient"]["custom_id"] if "patient" in appointment and "custom_id" in appointment[
                "patient"] else None
            doctor_name = appointment["doctor_data"]["user"]["first_name"] if appointment.get("doctor_data",
                                                                                              None) and \
                                                                              appointment.get("doctor_data").get(
                                                                                  "user", None) and \
                                                                              appointment.get("doctor_data").get(
                                                                                  "user").get(
                                                                                  "first_name", None) else "--"
            category_name = appointment["category_data"]["name"] if appointment.get("category_data",
                                                                                    None) and appointment.get(
                "category_data").get("name", None) else "--"
            ready_data.append({"S. No.": index + 1,
                               "Date": schedule_date,
                               "Patient Id": patient_id,
                               "Patient": patient_name,
                               "Schedule At": schedule_time,
                               "Current Status": appointment["status"] if appointment["status"] else "--",
                               "Doctor": doctor_name,
                               "Check-in At": checked_in,
                               "Waited For (hh:mm:ss)": waited,
                               "Engaged At": engaged,
                               "Checked Out": checked_out,
                               "Category": category_name})
        error, msg = dict_to_mail(ready_data, "All_Appointment_Report_" + start + "_" + end, mail_to, subject, body)
        response_dict = {"detail": msg, "error": error}
    else:
        response_dict = {
            "total": appointments.count(),
            "data": AppointmentSerializer(appointments, many=True).data,
            "error": False
        }
    return response_dict


def update_pratice_related_calender_object(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy()
    new_data_request['practice'] = instance.pk
    filetags_id = new_data_request.pop('id', None)
    if filetags_id:
        filetags_object = model_class.objects.get(id=filetags_id)
        is_delete = new_data_request.pop('is_delete', None)
        if is_delete:
            filetags_object.delete()
            return {'detail': 'Object Deleted Successfully'}
        serializer = serializer_class(instance=filetags_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data
    else:
        serializer = serializer_class(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()

        if request.data.get('session_list'):
            session_list = []
            seesions_data_list = request.data.get('session_list')
            for session in seesions_data_list:
                session_obj, flag = WeeklySessions.objects.get_or_create(**session)
                session_list.append(session_obj.pk)
            update_object.sessions = session_list
            update_object.save()

        serializer = serializer_class(data=new_data_request)
        return serializer_class(instance=update_object).data


def update_prescription_template(instance, request):
    new_data_request = request.data.copy()
    new_data_request['practice'] = instance.pk
    prescription_id = new_data_request.pop('id', None)
    if prescription_id:
        prescription_object = PrescriptionTemplate.objects.get(id=prescription_id)
        serializer = PrescriptionTemplateSerializer(instance=prescription_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return PrescriptionTemplateSerializer(instance=update_object).data
    else:
        advices = new_data_request.pop('advice_data', None)
        drugs = new_data_request.pop('drug', [])
        serializer = PrescriptionTemplateSerializer(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        if advices:
            for advice in advices:
                update_object.advice_data.get_or_create(details=advice)
        if drugs:
            for drug in drugs:
                drug = DrugCatalogTemplateSerializer(data=drug)
                drug.is_valid(raise_exception=True)
                drug = drug.save()
                update_object.drugs.add(DrugCatalogTemplate.objects.get(id=drug.id))
        return PrescriptionTemplateSerializer(instance=update_object).data


def payment_capture(payment_id, amount):
    razorpay_url = "https://api.razorpay.com/v1/payments/"
    response = requests.get(razorpay_url + payment_id, auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
    pay_response = json.loads(response.text)
    if amount * 100 != pay_response["amount"]:
        return {"detail": "Amount of the Payment does not matches amount of the order", "error": True}
    if pay_response["status"] == "authorized":
        data = {
            'amount': int(amount * 100)
        }
        capture_response = requests.post(razorpay_url + payment_id + '/capture', data=data,
                                         auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))
        capture = json.loads(capture_response.text)
        if "status" in capture and capture["status"] == "captured":
            return {"detail": "Payment Successful", "error": False}
        else:
            return {"detail": "Some Error Occurred", "error": True}
    elif pay_response["status"] == "captured":
        return {"detail": "This payment is already captured.", "error": True}
    elif pay_response["status"] == "failed":
        return {"detail": "Payment is failed", "error": True}


def dict_to_mail(data, report_name, mail_to, subject, body):
    if len(data) > 0:
        header = tuple(data[0].keys())
        path = os.path.join(settings.MEDIA_ROOT, report_name + ".csv")
        is_superuser = PracticeStaff.objects.filter(user__email=mail_to, is_active=True, user__is_active=True,
                                                    user__is_superuser=True).first()
        staff = PracticeStaff.objects.filter(user__email=mail_to, is_active=True, user__is_active=True)
        allowed = PracticeUserPermissions.objects.filter(codename=CONST_REPORT_MAIL, is_active=True,
                                                         staff__user__email=mail_to).count()
        if is_superuser or (staff.count() > 0 and allowed):
            staff_name = staff.first().user.first_name
            body = "Dear <b>" + staff_name + "</b>,<br/><br/>" + body
            with open(path, 'w') as outfile:
                writer = DictWriter(outfile, header)
                writer.writeheader()
                writer.writerows(data)
            email.send(mail_to, subject, body, "", [open(path, 'r')])
            os.remove(path)
            return False, "Mail Sent Successfully to " + mail_to
        elif staff.count() == 0:
            return True, "No staff exists with this mail"
        else:
            return True, "You do not have permissions to send reports on mail"
    else:
        return True, "No data available for mailing"


def send_notification(user, practice, application, title, body, open_screen=None, detail_id=None, icon=None,
                      image_link=None, device=None):
    if isinstance(user, int):
        user = User.objects.get(id=user)
    if isinstance(practice, int):
        practice = Practice.objects.get(id=practice)
    PushNotifications.objects.create(user=user, application=application, title=title, body=body, icon=icon,
                                     practice=practice, image_link=image_link, device=device, open_screen=open_screen,
                                     detail_id=detail_id)
    return
