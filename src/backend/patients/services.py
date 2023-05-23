import base64
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd
from ..appointment.models import Appointment
from ..base import response
from ..billing.serializers import PatientPaymentSerializer, PatientPaymentDataSerializer, \
    PatientInvoicesDataSerializer
from ..constants import CONST_CANCELLED
from .models import Patients, PatientInventory, GeneratedPdf, PatientInvoices, PatientTreatmentPlans, \
     PracticeStaff,Practice, PatientPayment, PatientPrescriptions, PatientFile, PatientProcedure, PatientVitalSigns, \
     PatientClinicNotes, PatientAdvice, InvoiceDetails, PatientWalletLedger
from .serializers import PatientsSerializer, PatientDrugsSerializer, PatientTreatmentPlansSerializer, \
    PatientVitalSignsSerializer, PatientClinicNotesDataSerializer, PatientProcedureDataSerializer, \
    PatientFileSerializer, PatientPrescriptionsDataSerializer
from ..practice.models import LabTestCatalog, PracticePrintSettings, EmailCommunications
from ..practice.serializers import PracticeComplaintsSerializer, \
    ObservationsSerializer, DiagnosesSerializer, InvestigationsSerializer, ExpenseTypeDataSerializer, \
    PracticeStaffSerializer, PracticeBasicDataSerializer, PracticeSerializer, EmailCommunicationsSerializer
from ..utils import pdf_document, timezone, email
from django.conf import settings
from django.db.models import Sum
from django.template.loader import get_template


def update_patient_procedure(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy()
    new_data_request['patient'] = instance.pk
    procedure_id = new_data_request.pop('id', None)
    treatment_plans = new_data_request.pop('treatment_plans', [])
    if procedure_id:
        procedure_object = model_class.objects.get(id=procedure_id)
        serializer = serializer_class(instance=procedure_object, data=new_data_request, partial=True)
    else:
        serializer = serializer_class(data=new_data_request, partial=True)
    serializer.is_valid(raise_exception=True)
    update_object = serializer.save()
    update_object.treatment_plans.set(PatientTreatmentPlans.objects.filter(id__in=[]))
    update_object.save()
    for treatment_plan in treatment_plans:
        treatment_plan_id = treatment_plan.pop("id", None)
        if treatment_plan_id:
            treatment_plan_obj = PatientTreatmentPlans.objects.get(id=treatment_plan_id)
            treatment_serializer = PatientTreatmentPlansSerializer(instance=treatment_plan_obj, data=treatment_plan,
                                                                   partial=True)
        else:
            treatment_serializer = PatientTreatmentPlansSerializer(data=treatment_plan, partial=True)
        treatment_serializer.is_valid(raise_exception=True)
        treatment_serializer = treatment_serializer.save()
        update_object.treatment_plans.add(treatment_serializer.id)
    return serializer_class(instance=update_object).data


def update_patient_prescriptions(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy()
    new_data_request['patient'] = instance.pk if instance else None
    prescription_id = request.data['id']
    # prescription_id = new_data_request.pop('id', None)
    print(type(prescription_id),prescription_id)
    labs = new_data_request.pop("labs", [])
    drugs = new_data_request.pop("drugs", [])
    advice_data = new_data_request.pop("advice_data", [])
    # new_data_request["advice_data"] = []
    if prescription_id:
        prescription_object = model_class.objects.get(id=prescription_id)
        serializer = serializer_class(instance=prescription_object, data=new_data_request, partial=True)
        print('d')
    else:
        serializer = serializer_class(data=new_data_request)
    serializer.is_valid(raise_exception=True)
    update_object = serializer.save()
    update_object.labs.set(LabTestCatalog.objects.filter(id__in=labs))
    update_object.drugs.set(PatientInventory.objects.filter(id__in=[]))
    update_object.advice_data.set(PatientAdvice.objects.filter(id__in=[]))
    update_object.save()
    if advice_data:
        for advice in advice_data:
            print('adding',advice)
            update_object.advice_data.create(details=advice)
    if drugs:
        for drug in drugs:
            patient_drug_id = drug.pop("id", None)
            if patient_drug_id:
                patient_drug_object = PatientInventory.objects.get(id=patient_drug_id)
                drug_serializer = PatientDrugsSerializer(instance=patient_drug_object, data=drug, partial=True)
            else:
                drug_serializer = PatientDrugsSerializer(data=drug, partial=True)
            drug_serializer.is_valid(raise_exception=True)
            drug_serializer = drug_serializer.save()
            update_object.drugs.add(PatientInventory.objects.get(id=drug_serializer.id))
    return serializer_class(instance=update_object).data


def update_pratice_patient_details(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy()
    new_data_request['practice'] = instance.pk if instance else None
    filetags_id = new_data_request.pop('id', None)
    if filetags_id:
        filetags_object = model_class.objects.get(id=filetags_id)
        serializer = serializer_class(instance=filetags_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data
    else:
        serializer = serializer_class(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data


def update_patient_extra_details(request, serializer_class, instance, model_class):
    new_data_request = request.data.copy() if not type(request) == type(dict()) else request
    new_data_request['patient'] = instance.pk if instance else None
    filetags_id = new_data_request.pop('id', None)
    if filetags_id:
        filetags_object = model_class.objects.get(id=filetags_id)
        serializer = serializer_class(instance=filetags_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data
    else:
        serializer = serializer_class(data=new_data_request)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data


def create_update_record(request, serializer_class, model_class):
    request_data = request.data.copy() if not type(request) == type(dict()) else request
    data_id = request_data.pop('id', None)
    if data_id:
        data_obj = model_class.objects.get(id=data_id)
        serializer = serializer_class(instance=data_obj, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data
    else:
        serializer = serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        update_object = serializer.save()
        return serializer_class(instance=update_object).data


def get_invoice_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    if start_date and end_date:
        invoices = instance.patientinvoices_set.filter(created_at__range=(start_date, end_date))
    else:
        invoices = instance.patientinvoices_set.all()
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        invoices = invoices.filter(order_by=sort_by)

    with_deleted = request.query_params.get('with_deleted', None)
    if not with_deleted:
        invoices = invoices.exclude(is_active=False)

    cancelled = request.query_params.get('cancelled', None)
    if not cancelled:
        invoices = invoices.exclude(is_cancelled=True)

    response_dict = {
        "total": invoices.count(),
        "data": PatientInvoicesDataSerializer(invoices, many=True).data
    }
    return response_dict


def get_payment_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    if start_date and end_date:
        payments = instance.patientpayment_set.filter(created_at__range=(start_date, end_date))
    else:
        payments = instance.patientpayment_set.all()
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        payments = payments.filter(order_by=sort_by)

    with_deleted = request.query_params.get('with_deleted', None)
    if not with_deleted:
        payments = payments.exclude(is_active=False)

    cancelled = request.query_params.get('cancelled', None)
    if not cancelled:
        payments = payments.exclude(is_cancelled=True)

    response_dict = {
        "total": payments.count(),
        "data": PatientPaymentDataSerializer(payments, many=True).data
    }
    return response_dict


def get_financial_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    payments = instance.patientpayment_set.filter(created_at__range=(start_date, end_date))
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        payments = payments.filter(order_by=sort_by)

    with_deleted = request.query_params.get('with_deleted', None)
    if not with_deleted:
        payments = payments.exclude(is_active=False)

    cancelled = request.query_params.get('cancelled', None)
    if not cancelled:
        payments = payments.exclude(is_cancelled=True)

    response_dict = {
        "total": payments.count(),
        "data": PatientPaymentDataSerializer(payments, many=True).data
    }
    return response_dict


def get_expense_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    expenses = instance.expensetype_set.filter(created_at__range=(start_date, end_date))
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        expenses = expenses.filter(order_by=sort_by)

    with_deleted = request.query_params.get('with_deleted', None)
    if not with_deleted:
        expenses = expenses.exclude(is_active=False)
    deleted = request.query_params.get('with_deleted', None)
    if deleted:
        expenses = expenses.filter(is_active=True)
    # cancelled = request.query_params.get('cancelled', None)
    # if not cancelled:
    #     payments = payments.exclude(is_cancelled=True)

    response_dict = {
        "total": expenses.count(),
        "data": ExpenseTypeDataSerializer(expenses, many=True).data
    }
    return response_dict


def get_patients_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)
    if start_date and end_date:
        payments = instance.patientpayment_set.filter(created_at__range=(start_date, end_date))
    else:
        payments = instance.patientpayment_set.all()
    sort_by = request.query_params.get('sort_on', None)
    if sort_by:
        payments = patients.filter(order_by=sort_by)

    response_dict = {
        "total": payments.count(),
        "data": PatientPaymentDataSerializer(payments, many=True).data
    }
    return response_dict


def get_treatment_report(instance, request):
    start_date = request.query_params.get('start', None)
    end_date = request.query_params.get('end', None)

    # complaints
    complaints = instance.practicecomplaints_set.filter(created_at__range=(start_date, end_date))
    complaints_data = PracticeComplaintsSerializer(complaints, many=True).data
    complaints_count = complaints.count()
    # observations
    observations = instance.observations_set.filter(created_at__range=(start_date, end_date))
    observations_data = ObservationsSerializer(observations, many=True).data
    observations_count = observations.count()
    # diagnosis 
    diagnosis = instance.diagnoses_set.filter(created_at__range=(start_date, end_date))
    diagnosis_data = DiagnosesSerializer(diagnosis, many=True).data
    diagnosis_count = diagnosis.count()

    # investigations
    investigations = instance.investigations_set.filter(created_at__range=(start_date, end_date))
    investigations_data = InvestigationsSerializer(investigations, many=True).data
    investigations_count = investigations.count()

    response_dict = {
        'complaints_data': complaints_data,
        'complaints_count': complaints_count,
        'observations_data': observations_data,
        'observations_count': observations_count,
        'diagnosis_data': diagnosis_data,
        'diagnosis_count': diagnosis_count,
        'investigations_data': investigations_data,
        'investigations_count': investigations_count
    }
    return response_dict


def generate_pdf(type, sub_type, model, serializer, id, practice, patient, doctor, template, name, extra_data=None):
    page_settings = PracticePrintSettings.objects.filter(type=type, sub_type=sub_type, practice=practice).order_by(
        "-modified_at").values()
    if page_settings:
        page_settings = page_settings[0]
    else:
        page_settings = {}
    if patient:
        patient_data = PatientsSerializer(Patients.objects.get(id=patient)).data
    else:
        patient_data = {}
    if doctor:
        doctor_data = PracticeStaffSerializer(PracticeStaff.objects.get(id=doctor)).data
    else:
        doctor_data = {}
    if practice:
        practice_data = PracticeBasicDataSerializer(Practice.objects.get(id=practice)).data
    else:
        practice_data = {}
    if id:
        model_data = serializer(instance=model.objects.get(id=id)).data
    else:
        model_data = None
    if model_data is None:
        model_data = model
    logo = None
    if page_settings and page_settings['logo_include']:
        logo = page_settings['logo_path']
        if logo and settings.SERVER == "PRODUCTION":
            s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            data = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=logo.replace('+', ' '))
            logo = base64.b64encode(data['Body'].read()).decode('ascii')
        elif logo:
            pngFile = open(os.path.join(settings.BASE_DIR, 'media', logo), 'rb')
            logo = base64.b64encode(pngFile.read()).decode('ascii')
    pdf_data = {
        'logo': logo,
        'page_settings': page_settings,
        'data': model_data,
        'extra_data': extra_data,
        'patient': patient_data,
        'doctor': doctor_data,
        'practice': practice_data,
        'time': timezone.now_local().strftime("%d/%m/%Y %I:%M %p")
    }
    template = get_template(template)
    pdf = pdf_document.html_to_pdf_convert(template, pdf_data)
    if id:
        pdf_obj, flag = GeneratedPdf.objects.get_or_create(name=name + str(id))
        pdf_obj.report.save("%s-%s.pdf" % (pdf_obj.uuid, id), pdf)
    else:
        pdf_obj, flag = GeneratedPdf.objects.get_or_create(name=name + str(patient))
        pdf_obj.report.save("%s-%s.pdf" % (pdf_obj.uuid, patient), pdf)
    if not settings.SERVER == "PRODUCTION":
        pdf.flush()
    return pdf_obj


def generate_timeline(instance, request):
    from ..appointment.serializers import AppointmentSerializer
    from ..appointment.models import Appointment
    response_list = []
    practice = request.get('practice_id', None)
    if request.get('appointments'):
        data = Appointment.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        appointment_data = AppointmentSerializer(data, many=True).data
        for appointment in appointment_data:
            data = appointment.copy()
            data["sort_date"] = pd.to_datetime(data["schedule_at"]).date() if "schedule_at" in data and data[
                "schedule_at"] else datetime.today().date()
            data["type"] = "Appointments"
            response_list.append(data)
    if request.get('clinic_notes'):
        data = PatientClinicNotes.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        clinic_notes = PatientClinicNotesDataSerializer(data, many=True).data
        for clinic_note in clinic_notes:
            data = clinic_note.copy()
            data["sort_date"] = pd.to_datetime(data["date"]).date() if "date" in data and data[
                "date"] else datetime.today().date()
            data["type"] = "Clinical Notes"
            response_list.append(data)
    if request.get('files'):
        data = PatientFile.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        files = PatientFileSerializer(data, many=True).data
        for file in files:
            data = file.copy()
            data["sort_date"] = pd.to_datetime(data["created_at"]).date() if "created_at" in data and data[
                "created_at"] else datetime.today().date()
            data["type"] = "Files"
            response_list.append(data)
    if request.get('invoices'):
        data = PatientInvoices.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        invoices = PatientInvoicesDataSerializer(data, many=True).data
        for invoice in invoices:
            data = invoice.copy()
            data["sort_date"] = pd.to_datetime(data["created_at"]).date() if "created_at" in data and data[
                "created_at"] else datetime.today().date()
            data["type"] = "Invoices"
            response_list.append(data)
    if request.get('payments'):
        data = PatientPayment.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        payments = PatientPaymentSerializer(data, many=True).data
        for payment in payments:
            data = payment.copy()
            data["sort_date"] = pd.to_datetime(data["created_at"]).date() if "created_at" in data and data[
                "created_at"] else datetime.today().date()
            data["type"] = "Payments"
            response_list.append(data)
    if request.get('prescriptions'):
        data = PatientPrescriptions.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        prescriptions = PatientPrescriptionsDataSerializer(data, many=True).data
        for prescription in prescriptions:
            data = prescription.copy()
            data["sort_date"] = pd.to_datetime(data["date"]).date() if "date" in data and data[
                "date"] else datetime.today().date()
            data["type"] = "Prescriptions"
            response_list.append(data)
    if request.get('procedures'):
        data = PatientProcedure.objects.filter(patient=instance, is_active=True, treatment_plans__is_completed=True)
        if practice:
            data = data.filter(practice=practice)
        procedures = PatientProcedureDataSerializer(data.distinct(), many=True).data
        for procedure in procedures:
            data = procedure.copy()
            data["sort_date"] = pd.to_datetime(data["date"]).date() if "date" in data and data[
                "date"] else datetime.today().date()
            data["type"] = "Procedures"
            response_list.append(data)
    if request.get('treatment_plans'):
        data = PatientProcedure.objects.filter(patient=instance, is_active=True, treatment_plans__is_completed=False)
        if practice:
            data = data.filter(practice=practice)
        procedures = PatientProcedureDataSerializer(data.distinct(), many=True).data
        for procedure in procedures:
            data = procedure.copy()
            data["sort_date"] = pd.to_datetime(data["date"]).date() if "date" in data and data[
                "date"] else datetime.today().date()
            data["type"] = "Treatment Plans"
            response_list.append(data)
    if request.get('vital_signs'):
        data = PatientVitalSigns.objects.filter(patient=instance, is_active=True)
        if practice:
            data = data.filter(practice=practice)
        vital_sign_data = PatientVitalSignsSerializer(data, many=True).data
        for vital_sign in vital_sign_data:
            data = vital_sign.copy()
            data["sort_date"] = pd.to_datetime(data["recorded_on"]).date() if "recorded_on" in data and data[
                "recorded_on"] else datetime.today().date()
            data["type"] = "Vital Signs"
            response_list.append(data)
    response_list.sort(key=lambda k: k["sort_date"], reverse=True)
    return response_list


def common_function(self, request, patient_id, practice_id, get_serializer, post_serializer, model, sort_on):
    if request.method == 'GET':
        data = model.objects.filter(is_active=True)
        if patient_id:
            data = data.filter(patient=patient_id)
        if practice_id:
            data = data.filter(practice=practice_id)
        if sort_on:
            data = data.order_by(sort_on, '-id')
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(get_serializer(page, many=True).data)
        return response.Ok(get_serializer(data, many=True).data)
    else:
        if patient_id:
            patient_instance = Patients.objects.get(id=patient_id)
            update_response = update_patient_extra_details(request, post_serializer, patient_instance, model)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send patient with data'})
        else:
            return response.BadRequest({'detail': 'Send patient with data'})


def generate_app_report(practice, start, end):
    start_date = pd.to_datetime(start).date()
    end_date = pd.to_datetime(end).date()
    diff = (end_date - start_date).days
    prev_start = start_date - timedelta(days=diff + 1)
    prev_end = start_date - timedelta(days=1)
    appointment_data = get_appointments(practice, start_date, end_date, False)
    last_count = get_appointments(practice, prev_start, prev_end, True)
    last_total = last_count["total"]
    appointment_total = appointment_data["total"]
    appointment_data["change"] = round((appointment_total - last_total) / last_total * 100) if last_total else 0
    invoice_data = get_invoices(practice, start_date, end_date, False)
    last_invoices = get_invoices(practice, prev_start, prev_end, True)
    current_sum = invoice_data["revenue"]
    last_sum = last_invoices["revenue"]
    invoice_data["change"] = round((current_sum - last_sum) / last_sum * 100) if last_sum else 0
    return {"appointments": appointment_data, "revenue": invoice_data}


def get_invoices(practice, start, end, only_total):
    output = {}
    start_time = timezone.get_day_start(start)
    end_time = timezone.get_day_end(end)
    queryset = PatientInvoices.objects.filter(is_active=True, is_cancelled=False)
    if start_time and end_time:
        queryset = queryset.filter(date__range=[start_time, end_time])
    if practice:
        queryset = queryset.filter(practice=practice)
    invoice_sum = queryset.aggregate(total=Sum('total'))
    output["revenue"] = round(invoice_sum["total"], 2) if invoice_sum["total"] else 0
    if not only_total:
        invoices = queryset.values_list('id', flat=True)
        paid = InvoiceDetails.objects.filter(invoice__in=invoices, is_active=True).aggregate(total=Sum("pay_amount"))
        output["paid"] = round(paid["total"], 2) if paid["total"] else 0
        output["pending"] = output["revenue"] - output["paid"]
    return output


def get_appointments(practice, start, end, only_total):
    output = {}
    start_time = timezone.get_day_start(start)
    end_time = timezone.get_day_end(end)
    queryset = Appointment.objects.filter(is_active=True)
    if start_time and end_time:
        queryset = queryset.filter(schedule_at__range=[start_time, end_time])
    if practice:
        queryset = queryset.filter(practice=practice)
    output["total"] = queryset.count()
    if not only_total:
        count = 0
        for appointment in queryset:
            first = Appointment.objects.filter(patient=appointment.patient, id__lt=appointment.id,
                                               is_active=True).count()
            count += 1 if first == 0 else 0
        output["cancelled"] = queryset.filter(status=CONST_CANCELLED).count()
        output["booked"] = output["total"] - output["cancelled"]
        output["new_patients"] = count
        output["old_patients"] = output["total"] - count
    return output


def get_advisor_sale(patients, start, end):
    result = {}
    invoices = PatientWalletLedger.objects.filter(patient__in=patients, created_at__range=[start, end],
                                                  is_cancelled=False, ledger_type='Credit') \
        .values_list('invoice', flat=True).distinct()
    invoice_data = PatientInvoices.objects.filter(id__in=invoices).values('id', 'patient__user__referer', 'total',
                                                                          'patient__user', 'patient__is_approved')
    for invoice in invoice_data:
        if invoice['patient__is_approved']:
            if invoice['patient__user'] in result:
                result[invoice['patient__user']] += invoice['total']
            else:
                result[invoice['patient__user']] = invoice['total']
        else:
            if invoice['patient__user__referer'] in result:
                result[invoice['patient__user__referer']] += invoice['total']
            else:
                result[invoice['patient__user__referer']] = invoice['total']
    return result


def mail_file(patient_name, mail_to, pdf_obj, practice, report_name):
    html = get_template('email_content.html')
    if practice:
        communications = EmailCommunications.objects.filter(practice=practice, is_active=True)
        if not communications.exists():
            return {"error": True, "detail": "Please set details in communication settings"}
        practice_details = PracticeSerializer(Practice.objects.filter(id=practice).first()).data
        communication_details = EmailCommunicationsSerializer(communications.order_by("-id").first()).data
        data = {"practice": practice_details, "communications": communication_details, "name": patient_name,
                "report_name": report_name, "base_url": settings.DOMAIN + settings.MEDIA_URL}
    else:
        return {"error": True, "detail": "Invalid Clinic Selected"}
    if pdf_obj:
        html_content = html.render(data)
        subject = report_name + " from " + practice_details["name"]
        file = pdf_obj.report
        email.send(mail_to, subject, html_content, "", [file])
        return {"error": False, "detail": "Mail Sent Successfully"}
    else:
        return {"error": True, "detail": "Failed to generate mail document"}
