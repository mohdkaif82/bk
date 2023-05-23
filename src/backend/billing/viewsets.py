import csv
import os
from datetime import datetime
from itertools import groupby
from operator import itemgetter

import pandas as pd
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from .permissions import BillingPermissions
from .serializers import PatientInvoicesDataSerializer, PatientInvoicesGetSerializer, \
    PatientPaymentSerializer, PatientInvoicesReportSerializer, PatientPaymentDataSerializer, PatientWalletSerializer, \
    PatientWalletLedgerSerializer, ReturnPaymentSerializer, PatientsPromoCodeSerializer
from ..constants import CONST_GLOBAL_PRACTICE
from ..inventory.models import InventoryCsvReports
from ..inventory.serializers import InventoryCsvReportsSerializer
from ..patients.models import Patients, PatientInvoices, InvoiceDetails, PatientPayment, ReturnPayment, \
    PatientWalletLedger, PatientWallet, PatientsPromoCode
from ..patients.serializers import GeneratedPdfSerializer, PatientsBasicDataSerializer
from ..patients.services import generate_pdf, mail_file, common_function
from ..practice.models import Practice, PracticeStaff
from ..practice.services import dict_to_mail
from ..utils import pdf_document, sms
from django.conf import settings
from django.core.files.base import File
from django.db.models import Sum
from django.template import Template, Context
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser

from .models import PatientProformaInvoices
from .serializers import PatientProformaInvoicesDataSerializer, PatientProformaInvoicesGetSerializer


class PatientProformaInvoicesViewSet(ModelViewSet):
    serializer_class = PatientProformaInvoicesDataSerializer
    queryset = PatientProformaInvoices.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientProformaInvoicesViewSet, self).get_queryset()
        patient_id = self.request.query_params.get('patient', None)
        practice_id = self.request.query_params.get('practice', None)
        is_pending = self.request.query_params.get('is_pending', None)
        is_cancelled = self.request.query_params.get('is_cancelled', None)
        doctors = self.request.query_params.get('doctor', None)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        summary = self.request.query_params.get('summary', None)
        is_pending = True if is_pending == "true" else False
        summary = True if summary == "true" else False
        if summary:
            self.serializer_class = PatientProformaInvoicesGetSerializer
        queryset = queryset.filter(is_active=True)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if practice_id:
            queryset = queryset.filter(practice__id=practice_id)
            practice = Practice.objects.get(id=practice_id)
            hide_cancelled = practice.hide_cancelled_proforma
            if hide_cancelled:
                queryset = queryset.exclude(is_cancelled=True)
        if is_pending:
            queryset = queryset.filter(is_pending=is_pending)
        if is_cancelled:
            is_cancelled = True if is_cancelled == "true" else False
            queryset = queryset.filter(is_cancelled=is_cancelled)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(procedure__doctor__in=doctor_list) | queryset.filter(
                inventory__doctor__in=doctor_list)
            queryset = queryset.distinct()
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
        return queryset.order_by('-date', '-id')

    @action(methods=['GET'], detail=True)
    def get_pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        patient_name = instance.patient.user.first_name if instance.patient and instance.patient.user else "User"
        mail_to = request.query_params.get("mail_to", None)
        practice = instance.practice.pk if instance.practice else None
        patient = instance.patient.pk if instance.patient else None
        pdf_obj = generate_pdf("BILLING", "INVOICE", PatientProformaInvoices, PatientProformaInvoicesDataSerializer,
                               instance.pk, practice, patient, None, "proforma_invoice.html", "ProformaInvoiceID")

        result = GeneratedPdfSerializer(pdf_obj).data
        if mail_to:
            result = mail_file(patient_name, mail_to, pdf_obj, practice, "Invoice")
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET'], detail=False)
    def update_id(self, request, *args, **kwargs):
        queryset = PatientProformaInvoices.objects.all().order_by("id")
        for obj in queryset:
            prefix = obj.practice.proforma_prefix if obj and obj.practice and obj.practice.proforma_prefix else ""
            invoice_id = prefix + str(
                PatientProformaInvoices.objects.filter(practice=obj.practice, id__lte=obj.pk).count())
            PatientProformaInvoices.objects.filter(id=obj.pk).update(invoice_id=invoice_id)
        return response.Ok({"detail": "Updated"})


class PatientInvoicesViewSet(ModelViewSet):
    serializer_class = PatientInvoicesDataSerializer
    queryset = PatientInvoices.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientInvoicesViewSet, self).get_queryset()
        patient_id = self.request.query_params.get('patient', None)
        practice_id = self.request.query_params.get('practice', None)
        is_pending = self.request.query_params.get('is_pending', None)
        is_cancelled = self.request.query_params.get('is_cancelled', None)
        doctors = self.request.query_params.get('doctor', None)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        summary = self.request.query_params.get('summary', None)
        is_pending = True if is_pending == "true" else False
        summary = True if summary == "true" else False
        if summary:
            self.serializer_class = PatientInvoicesGetSerializer
        queryset = queryset.filter(is_active=True)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if practice_id:
            queryset = queryset.filter(practice__id=practice_id)
            practice = Practice.objects.get(id=practice_id)
            hide_cancelled = practice.hide_cancelled_invoice
            if hide_cancelled:
                queryset = queryset.exclude(is_cancelled=True)
        if is_pending:
            queryset = queryset.filter(is_pending=is_pending)
        if is_cancelled:
            is_cancelled = True if is_cancelled == "true" else False
            queryset = queryset.filter(is_cancelled=is_cancelled)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(procedure__doctor__in=doctor_list) | queryset.filter(
                inventory__doctor__in=doctor_list)
            queryset = queryset.distinct()
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
        return queryset.order_by('-date', '-id')

    @action(methods=['GET'], detail=True)
    def get_pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        patient_name = instance.patient.user.first_name if instance.patient and instance.patient.user else "User"
        mail_to = request.query_params.get("mail_to", None)
        practice = instance.practice.pk if instance.practice else None
        patient = instance.patient.pk if instance.patient else None
        pdf_obj = generate_pdf("BILLING", "INVOICE", PatientInvoices, PatientInvoicesDataSerializer, instance.pk,
                               practice, patient, None, "invoice.html", "InvoiceID")

        result = GeneratedPdfSerializer(pdf_obj).data
        if mail_to:
            result = mail_file(patient_name, mail_to, pdf_obj, practice, "Invoice")
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET'], detail=False)
    def update_id(self, request, *args, **kwargs):
        queryset = PatientInvoices.objects.all().order_by("id")
        for obj in queryset:
            prefix = obj.practice.invoice_prefix if obj and obj.practice and obj.practice.invoice_prefix else ""
            invoice_id = prefix + str(PatientInvoices.objects.filter(practice=obj.practice, id__lte=obj.pk).count())
            PatientInvoices.objects.filter(id=obj.pk).update(invoice_id=invoice_id)
        return response.Ok({"detail": "Updated"})

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def invoice_reports(self, request, *args, **kwargs):
        practice_id = request.query_params.get('practice', None)
        is_cancelled = request.query_params.get('is_cancelled', None)
        income_type = request.query_params.get('income_type', None)
        report_type = request.query_params.get('type', None)
        doctors = request.query_params.get('doctors', None)
        groups = request.query_params.get('groups', None)
        treatments = request.query_params.get('treatments', None)
        products = request.query_params.get('products', None)
        taxes = request.query_params.get('taxes', None)
        discount = request.query_params.get('discount', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        queryset = PatientInvoices.objects.filter(is_active=True)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if practice_id:
            queryset = queryset.filter(practice=practice_id)
            instance = Practice.objects.filter(id=practice_id).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if is_cancelled:
            is_cancelled = True if is_cancelled == "true" else False
            queryset = queryset.filter(is_cancelled=is_cancelled)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(inventory__doctor__in=doctor_list) | queryset.filter(
                procedure__doctor__in=doctor_list)
        if groups:
            group_list = groups.split(",")
            patients = Patients.objects.filter(patient_group__in=group_list).values_list('id', flat=True)
            queryset = queryset.filter(patient__in=patients)
        if treatments:
            treatment_list = treatments.split(",")
            queryset = queryset.filter(procedure__procedure__in=treatment_list)
        if products:
            product_list = products.split(",")
            queryset = queryset.filter(inventory__inventory__in=product_list)
        if taxes:
            tax_list = taxes.split(",")
            queryset = queryset.filter(procedure__taxes__in=tax_list) | queryset.filter(inventory__taxes__in=tax_list)
        if discount and discount == "ZERO":
            queryset = queryset.filter(procedure__discount_value__lt=1) | queryset.filter(
                inventory__discount_value__lt=1)
        elif discount and discount == "NON_ZERO":
            queryset = queryset.filter(procedure__discount_value__gt=1) | queryset.filter(
                inventory__discount_value__gt=1)
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
        if income_type and income_type == "PRODUCTS":
            queryset = queryset.exclude(inventory=None)
        elif income_type and income_type == "SERVICES":
            queryset = queryset.exclude(procedure=None)
        elif income_type and income_type == "RESERVATION":
            queryset = queryset.exclude(reservation=None)
        queryset = queryset.distinct()
        if report_type == "ALL":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            if mail_to:
                for index, item in enumerate(res):
                    treatments = ""
                    for procedure in item["procedure"]:
                        treatments += procedure["name"] + "," if "name" in procedure else ""
                    for inventory in item["inventory"]:
                        treatments += inventory["name"] + "," if "name" in inventory else ""
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Date": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if item['date'] else "--",
                        "Invoice Number": item["invoice_id"],
                        "Patient Name": item["patient"]["user"]["first_name"] if "patient" in item else "--",
                        "Patient ID": item["patient"]["custom_id"] if "patient" in item else "--",
                        "Treatment & Products": treatments,
                        "Total Amount": round(item["total"], 2),
                    })
                subject = "Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Income_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                res = {"detail": msg, "error": error}
            if "error" in res and res["error"]:
                return response.BadRequest(res)
            return response.Ok(res)
        if report_type == "DAILY":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                value = self.calculate_total(item)
                if item["date"] and item["date"] in filter_data:
                    filter_data[item["date"]]["cost"] += value["cost"]
                    filter_data[item["date"]]["tax"] += value["tax"]
                    filter_data[item["date"]]["discount"] += value["discount"]
                elif item["date"]:
                    filter_data[item["date"]] = value
            keys = list(filter_data.keys())
            keys.sort()
            for date in keys:
                data.append({"date": date, **filter_data[date]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Day": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if item['date'] else "--",
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Daily Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Income_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "MONTHLY":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                value = self.calculate_total(item)
                item_date = item["date"][:-3] if item["date"] else "NA"
                if item_date in filter_data:
                    filter_data[item_date]["cost"] += value["cost"]
                    filter_data[item_date]["tax"] += value["tax"]
                    filter_data[item_date]["discount"] += value["discount"]
                else:
                    filter_data[item_date] = value
            keys = list(filter_data.keys())
            keys.sort()
            for date in keys:
                data.append({"date": date + "-01", **filter_data[date]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Day": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if item['date'] else "--",
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Monthly Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Income_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "TAX":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    total_tax = 0
                    for tax in inv["taxes_data"]:
                        total_tax += tax["tax_value"]
                    for tax in inv["taxes_data"]:
                        if tax["id"] in filter_data:
                            filter_data[tax["id"]]["total"] += inv["tax_value"] * tax["tax_value"] / total_tax
                        else:
                            filter_data[tax["id"]] = {"name": tax["name"], "tax_value": tax["tax_value"],
                                                      "total": inv["tax_value"] * tax["tax_value"] / total_tax}
                for procedure in item["procedure"]:
                    total_tax = 0
                    for tax in procedure["taxes_data"]:
                        total_tax += tax["tax_value"]
                    for tax in procedure["taxes_data"]:
                        if tax["id"] in filter_data:
                            filter_data[tax["id"]]["total"] += inv["tax_value"] * tax["tax_value"] / total_tax
                        else:
                            filter_data[tax["id"]] = {"name": tax["name"], "tax_value": tax["tax_value"],
                                                      "total": inv["tax_value"] * tax["tax_value"] / total_tax}
                if item["reservation"]:
                    bed_package = item["reservation_data"]["bed_package"]
                    # add code for bed booking after discount tax will change
            keys = list(filter_data.keys())
            keys.sort()
            for tax_id in keys:
                data.append({"id": tax_id, **filter_data[tax_id]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No.": index + 1,
                        "Tax Name": item["name"] if item['name'] else "--",
                        "Tax Value": str(item["tax_value"]) + "%" if item['tax_value'] else "--",
                        "Tax(INR)": round(item["total"], 2)
                    })
                subject = "Taxed Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Taxed_Income_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "DOCTOR":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    doctor_id = str(inv["doctor"]) if inv["doctor"] else "NA"
                    if doctor_id in filter_data:
                        filter_data[doctor_id]["cost"] += inv["total"] - inv["tax_value"]
                        filter_data[doctor_id]["discount_value"] += inv["discount_value"]
                        filter_data[doctor_id]["tax_value"] += inv["tax_value"]
                    else:
                        filter_data[doctor_id] = {"cost": inv["total"] - inv["tax_value"],
                                                  "discount_value": inv["discount_value"],
                                                  "tax_value": inv["tax_value"]}
                for procedure in item["procedure"]:
                    doctor_id = str(procedure["doctor"]) if procedure["doctor"] else "NA"
                    if doctor_id in filter_data:
                        filter_data[doctor_id]["cost"] += procedure["total"] - procedure["tax_value"]
                        filter_data[doctor_id]["discount_value"] += procedure["discount_value"]
                        filter_data[doctor_id]["tax_value"] += procedure["tax_value"]
                    else:
                        filter_data[doctor_id] = {"cost": procedure["total"] - procedure["tax_value"],
                                                  "discount_value": procedure["discount_value"],
                                                  "tax_value": procedure["tax_value"]}
                if item["reservation"]:
                    doctor_id = "NA"
                    total = item["total"] if "total" in item and item["total"] else 0
                    discount_value = item["discount"] if "discount" in item and item["discount"] else 0
                    tax_value = item["taxes"] if "taxes" in item and item["taxes"] else 0
                    if doctor_id in filter_data:
                        filter_data[doctor_id]["cost"] += total - tax_value
                        filter_data[doctor_id]["discount_value"] += discount_value
                        filter_data[doctor_id]["tax_value"] += tax_value
                    else:
                        filter_data[doctor_id] = {"cost": total - tax_value, "discount_value": discount_value,
                                                  "tax_value": tax_value}
            keys = list(filter_data.keys())
            keys.sort()
            for doctor in keys:
                data.append({"doctor": doctor, **filter_data[doctor]})
            if mail_to:
                for index, item in enumerate(data):
                    doctor_name = PracticeStaff.objects.filter(id=item["doctor"]).first().user.first_name
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Doctor": doctor_name,
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Doctor Wise Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Doctor_Wise_Income_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PROCEDURE":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, "SERVICES", doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for procedure in item["procedure"]:
                    procedure_id = procedure["procedure"] if procedure["procedure"] else "NA"
                    if procedure_id in filter_data:
                        filter_data[procedure_id]["cost"] += procedure["total"] - procedure["tax_value"]
                        filter_data[procedure_id]["discount_value"] += procedure["discount_value"]
                        filter_data[procedure_id]["tax_value"] += procedure["tax_value"]
                    else:
                        filter_data[procedure_id] = {"cost": procedure["total"] - procedure["tax_value"],
                                                     "discount_value": procedure["discount_value"],
                                                     "tax_value": procedure["tax_value"],
                                                     "name": procedure["name"]}
            keys = list(filter_data.keys())
            for procedure in keys:
                data.append({"procedure": procedure, **filter_data[procedure]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Treatment Category": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Procedure Wise Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Procedure_Wise_Income_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PRODUCT":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, "PRODUCTS", doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    inv_id = inv["inventory"] if inv["inventory"] else "NA"
                    if inv_id in filter_data:
                        filter_data[inv_id]["cost"] += inv["total"] - inv["tax_value"]
                        filter_data[inv_id]["discount_value"] += inv["discount_value"]
                        filter_data[inv_id]["tax_value"] += inv["tax_value"]
                    else:
                        filter_data[inv_id] = {"cost": inv["total"] - inv["tax_value"],
                                               "discount_value": inv["discount_value"],
                                               "tax_value": inv["tax_value"],
                                               "name": inv["name"]}
            keys = list(filter_data.keys())
            for product in keys:
                data.append({"product": product, **filter_data[product]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Product Name": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Product Wise Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Product_Wise_Income_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PATIENT_GROUPS":
            data = PatientInvoicesReportSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                patient_id = item["patient"]["id"] if item["patient"] else None
                if patient_id:
                    patient = Patients.objects.get(id=patient_id)
                    patient_groups = patient.patient_group.all()
                    if len(patient_groups) > 0:
                        value = self.calculate_total(item)
                    for group in patient_groups:
                        if group in filter_data:
                            filter_data[group.id]["cost"] += value["cost"]
                            filter_data[group.id]["discount_value"] += value["discount_value"]
                            filter_data[group.id]["tax_value"] += value["tax_value"]
                        else:
                            filter_data[group.id] = value
                            filter_data[group.id]["name"] = group.name
            keys = list(filter_data.keys())
            for patient_groups in keys:
                data.append({"group_id": patient_groups, **filter_data[patient_groups]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Patient Group": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Income after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Income Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Patient Group Income Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Group_Income_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})

    def calculate_total(self, data):
        total = 0
        tax_value = 0
        discount_value = 0
        for inv in data["inventory"]:
            total += inv["total"]
            discount_value += inv["discount_value"]
            tax_value += inv["tax_value"]
        for procedure in data["procedure"]:
            total += procedure["total"]
            discount_value += procedure["discount_value"]
            tax_value += procedure["tax_value"]
        if data["reservation"]:
            total += data["total"] if "total" in data and data["total"] else 0
            discount_value += data["discount"] if "discount" in data and data["discount"] else 0
            tax_value += data["taxes"] if "taxes" in data and data["taxes"] else 0
        return {"cost": total - tax_value, "tax": tax_value, "discount": discount_value}

    def data_filter(self, data, income_type, doctors, treatments, products, taxes, discount):
        res = []
        for item in data:
            if income_type and income_type == "PRODUCTS":
                item["procedure"] = []
            elif income_type and income_type == "SERVICES":
                item["inventory"] = []
            if doctors:
                doctor_list = doctors.split(",")
                doctor_list = list(map(int, doctor_list))
                inv_items = []
                for inv in item["inventory"]:
                    if inv["doctor"] in doctor_list:
                        inv_items.append(inv)
                item["inventory"] = inv_items
                procedure_items = []
                for procedure in item["procedure"]:
                    if procedure["doctor"] in treatment_list:
                        procedure_items.append(procedure)
                item["procedure"] = procedure_items
            if products:
                product_list = products.split(",")
                product_list = list(map(int, product_list))
                inv_items = []
                for inv in item["inventory"]:
                    if inv["inventory"] in product_list:
                        inv_items.append(inv)
                item["inventory"] = inv_items
            if treatments:
                treatment_list = treatments.split(",")
                treatment_list = list(map(int, treatment_list))
                procedure_items = []
                for procedure in item["procedure"]:
                    if procedure["procedure"] in treatment_list:
                        procedure_items.append(procedure)
                item["procedure"] = procedure_items
            if taxes:
                tax_list = taxes.split(",")
                tax_list = list(map(int, tax_list))
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if len(list(set(inv["taxes"]).intersection(tax_list))) != 0:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if len(list(set(procedure["taxes"]).intersection(tax_list))) != 0:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            if discount and discount == "ZERO":
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if inv["discount_value"] < 1:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if procedure["discount_value"] < 1:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            elif discount and discount == "NON_ZERO":
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if inv["discount_value"] >= 1:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if procedure["discount_value"] >= 1:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            if len(item["inventory"]) != 0 or len(item["procedure"]) != 0 or item["reservation"] != None:
                res.append(item)
        return res

    @action(methods=['GET'], detail=False)
    def amount_due(self, request, *args, **kwargs):
        mail_to = request.query_params.get('mail_to', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        doctors = request.query_params.get('doctors', None)
        groups = request.query_params.get('groups', None)
        practice = request.query_params.get('practice', None)
        report_type = request.query_params.get('type', None)
        queryset = PatientInvoices.objects.filter(is_active=True, is_pending=True, is_cancelled=False)
        practice_name = CONST_GLOBAL_PRACTICE
        if start and end:
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            queryset = queryset.filter(date__range=[start_date, end_date])
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(staff__in=doctor_list)
        if groups:
            group_list = groups.split(",")
            patients = Patients.objects.filter(patient_group__in=group_list).values_list('id', flat=True)
            queryset = queryset.filter(patient__in=patients)
        if practice:
            queryset = queryset.filter(practice=practice)
            instance = Practice.objects.filter(id=practice).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        queryset = queryset.order_by('-date')
        data = []
        index = 0
        ready_data = []
        for obj in queryset:
            prefix = obj.practice.invoice_prefix if obj.practice and obj.practice.invoice_prefix else ""
            invoice_id = prefix + str(PatientInvoices.objects.filter(practice=obj.practice, id__lte=obj.id).count())
            pay_data = InvoiceDetails.objects.filter(invoice=obj, is_active=True,
                                                     patientpayment__is_cancelled=False,
                                                     patientpayment__is_active=True).aggregate(
                total=Sum('pay_amount'))
            paid = pay_data["total"] if pay_data["total"] else 0
            total = obj.total if obj.total else 0
            due = total - paid
            doctors_id = []
            doctors_name = []
            for item in obj.inventory.all():
                if item.doctor:
                    doctors_id.append(item.doctor.pk)
                    doctors_name.append(item.doctor.user.first_name)
            for item in obj.procedure.all():
                if item.doctor:
                    doctors_id.append(item.doctor.pk)
                    doctors_name.append(item.doctor.user.first_name)
            if len(doctors_id) > 0:
                doctor_id = max(set(doctors_id), key=doctors_id.count)
                doctor_name = max(set(doctors_name), key=doctors_name.count)
            else:
                doctor_id = 0
                doctor_name = "No Doctor"
            inv_data = {
                "id": obj.id,
                "invoice_id": invoice_id,
                "patient_id": obj.patient.pk if obj.patient else None,
                "first_name": obj.patient.user.first_name if obj.patient and obj.patient.user else None,
                "custom_id": obj.patient.custom_id if obj.patient else None,
                "mobile": obj.patient.user.mobile if obj.patient and obj.patient.user else None,
                "date": obj.date,
                "total": round(obj.total, 2),
                "amount_due": round(due, 2),
                "doctor_name": doctor_name,
                "doctor_id": doctor_id
            }
            if mail_to and report_type == "ALL":
                index += 1
                inv_data1 = {
                    "S. No.": index,
                    "Invoice Date": obj.date,
                    "Invoice Id": invoice_id,
                    "Patient Name": obj.patient.user.first_name if obj.patient and obj.patient.user else "--",
                    "Patient Id": obj.patient.custom_id if obj.patient else "--",
                    "Doctor Name": doctor_name,
                    "Invoice Amount": round(obj.total, 2),
                    "Amount Due": round(due, 2),
                    "Mobile No": obj.patient.user.mobile if obj.patient and obj.patient.user else "--",
                }
                ready_data.append(inv_data1)
            data.append(inv_data)
        if report_type == "ALL":
            result = data
            if mail_to:
                subject = "Amount Due Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Amount Due Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Amount_Due_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "AGEING":
            result = []
            ready_data = []
            index = 0
            data.sort(key=itemgetter('patient_id'))
            for patient_id, items in groupby(data, key=itemgetter('patient_id')):
                index += 1
                temp_data = {"patient_id": patient_id, "0_29": 0, "30_59": 0, "60_89": 0, "89_364": 0, "365": 0}
                temp_data1 = {
                    "S. No.": index,
                    "Patient Name": "",
                    "Patient Id": "",
                    "for 0-29 days (INR)": 0,
                    "for 30-59 days (INR)": 0,
                    "for 60-89 days (INR)": 0,
                    "for 89-364 days (INR)": 0,
                    "for more than 364 days (INR)": 0,
                    "Total (INR)": 0
                }
                for i in items:
                    temp_data["first_name"] = i["first_name"]
                    temp_data["custom_id"] = i["custom_id"]
                    temp_data1["Patient Name"] = i["first_name"]
                    temp_data1["Patient Id"] = i["custom_id"]
                    temp_data1["Total (INR)"] += i["amount_due"]
                    day_cnt = (datetime.today().date() - i["date"]).days
                    if day_cnt < 30:
                        temp_data["0_29"] += i["amount_due"]
                        temp_data1["for 0-29 days (INR)"] += i["amount_due"]
                    elif day_cnt < 60:
                        temp_data["30_59"] += i["amount_due"]
                        temp_data1["for 30-59 days (INR)"] += i["amount_due"]
                    elif day_cnt < 90:
                        temp_data["60_89"] += i["amount_due"]
                        temp_data1["for 60-89 days (INR)"] += i["amount_due"]
                    elif day_cnt < 365:
                        temp_data["89_364"] += i["amount_due"]
                        temp_data1["for 89-364 days (INR)"] += i["amount_due"]
                    else:
                        temp_data["365"] += i["amount_due"]
                        temp_data1["for more than 364 days (INR)"] += i["amount_due"]
                result.append(temp_data)
                ready_data.append(temp_data1)
            if mail_to:
                subject = "Ageing Amount Due Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Ageing Amount Due Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Ageing_Amount_Due_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DOCTOR":
            result = []
            ready_data = []
            index = 0
            data.sort(key=itemgetter('doctor_id'))
            for doctor_id, items in groupby(data, key=itemgetter('doctor_id')):
                index += 1
                temp_data = {"doctor_id": doctor_id, "invoiced": 0, "amount_due": 0}
                if mail_to:
                    temp_data1 = {"S. No.": index, "Doctor": "", "Invoiced (INR)": 0, "Received (INR)": 0,
                                  "Total Amount Due (INR)": 0}
                for i in items:
                    temp_data["doctor_name"] = i["doctor_name"]
                    temp_data["invoiced"] += i["total"]
                    temp_data["amount_due"] += i["amount_due"]
                    if mail_to:
                        temp_data1["Doctor"] = i["doctor_name"]
                        temp_data1["Invoiced (INR)"] += i["total"]
                        temp_data1["Total Amount Due (INR)"] += i["amount_due"]
                if mail_to:
                    temp_data1["Received (INR)"] = temp_data1["Invoiced (INR)"] - temp_data1["Total Amount Due (INR)"]
                    ready_data.append(temp_data1)
                result.append(temp_data)
            if mail_to:
                subject = "Doctor Wise Amount Due Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Doctor Wise Amount Due Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Doctor_Amount_Due_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})


class PatientPaymentViewSet(ModelViewSet):
    serializer_class = PatientPaymentSerializer
    queryset = PatientPayment.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientPaymentViewSet, self).get_queryset()
        patient_id = self.request.query_params.get('patient', None)
        practice_id = self.request.query_params.get('practice', None)
        queryset = queryset.filter(is_active=True)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if practice_id:
            queryset = queryset.filter(practice__id=practice_id)
            practice = Practice.objects.get(id=practice_id)
            hide_cancelled = practice.hide_cancelled_payment
            if hide_cancelled:
                queryset = queryset.exclude(is_cancelled=True)
        return queryset.order_by('-date', '-id')

    @action(methods=['GET'], detail=False)
    def get_payments(self, request, *args, **kwargs):
        patient_id = request.query_params.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        get_serializer = PatientPaymentDataSerializer
        post_serializer = None
        model = PatientPayment
        sort_on = "-date"
        return common_function(self, request, patient_id, practice_id, get_serializer, post_serializer, model, sort_on)

    @action(methods=['GET'], detail=False)
    def update_id(self, request, *args, **kwargs):
        queryset = PatientPayment.objects.all().order_by("id")
        for obj in queryset:
            prefix = obj.practice.payment_prefix if obj and obj.practice and obj.practice.payment_prefix else ""
            payment_id = prefix + str(PatientPayment.objects.filter(practice=obj.practice, id__lte=obj.pk).count())
            PatientPayment.objects.filter(id=obj.pk).update(payment_id=payment_id)
        return response.Ok({"detail": "Updated"})

    @action(methods=['GET'], detail=True)
    def get_pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        patient_name = instance.patient.user.first_name if instance.patient and instance.patient.user else "User"
        mail_to = request.query_params.get("mail_to", None)
        practice = instance.practice.pk if instance.practice else None
        patient = instance.patient.pk if instance.patient else None
        pdf_obj = generate_pdf("BILLING", "RECEIPTS", PatientPayment, PatientPaymentDataSerializer, instance.pk,
                               practice, patient, None, "payment.html", "PaymentID")
        result = GeneratedPdfSerializer(pdf_obj).data
        if mail_to:
            result = mail_file(patient_name, mail_to, pdf_obj, practice, "Receipts")
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['POST'], detail=False)
    def bulk_payments(self, request, *args, **kwargs):
        data = request.data.copy()
        save_data = []
        for record in data:
            payment_id = record.pop("id", None)
            if payment_id:
                payment_obj = PatientPayment.objects.get(id=payment_id)
                serializer = PatientPaymentSerializer(data=record, instance=payment_obj, partial=True)
            else:
                serializer = PatientPaymentSerializer(data=record, partial=True)
            serializer.is_valid(raise_exception=True)
            save_data.append(serializer)
        for record in save_data:
            record.save()
        return response.Ok({"detail": "Payment Completed Successfully"})

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def payment_reports(self, request, *args, **kwargs):
        practice_id = request.query_params.get('practice', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        is_cancelled = request.query_params.get('is_cancelled', None)
        report_type = request.query_params.get('type', None)
        doctors = request.query_params.get('doctors', None)
        groups = request.query_params.get('groups', None)
        treatments = request.query_params.get('treatments', None)
        products = request.query_params.get('products', None)
        taxes = request.query_params.get('taxes', None)
        discount = request.query_params.get('discount', None)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        queryset = PatientPayment.objects.filter(is_active=True)
        if practice_id:
            queryset = queryset.filter(practice=practice_id)
            instance = Practice.objects.filter(id=practice_id).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if is_cancelled:
            is_cancelled = True if is_cancelled == "true" else False
            queryset = queryset.filter(is_cancelled=is_cancelled)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(invoices__invoice__inventory__doctor__in=doctor_list) | queryset.filter(
                invoices__invoice__procedure__doctor__in=doctor_list)
        if groups:
            group_list = groups.split(",")
            patients = Patients.objects.filter(patient_group__in=group_list).values_list('id', flat=True)
            queryset = queryset.filter(patient__in=patients)
        if treatments:
            treatment_list = treatments.split(",")
            queryset = queryset.filter(invoices__invoice__procedure__procedure__in=treatment_list)
        if products:
            product_list = products.split(",")
            queryset = queryset.filter(invoices__invoice__inventory__inventory__in=product_list)
        if taxes:
            tax_list = taxes.split(",")
            queryset = queryset.filter(invoices__invoice__procedure__taxes__in=tax_list) | queryset.filter(
                invoices__invoice__inventory__taxes__in=tax_list)
        if discount and discount == "ZERO":
            queryset = queryset.filter(invoices__invoice__procedure__discount_value__lt=1) | queryset.filter(
                invoices__invoice__inventory__discount_value__lt=1)
        elif discount and discount == "NON_ZERO":
            queryset = queryset.filter(invoices__invoice__procedure__discount_value__gt=1) | queryset.filter(
                invoices__invoice__inventory__discount_value__gt=1)
        if start and end:
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            queryset = queryset.filter(date__range=[start_date, end_date])
        ready_data = []
        if report_type == "ALL":
            result = PatientPaymentDataSerializer(queryset.order_by("-date"), many=True).data
            for item in result:
                for invoice in item['invoices']:
                    invoice_items = ""
                    for procedure_item in invoice['invoice']['procedure']:
                        item_name = procedure_item["name"]
                        doctor_name = " By Dr. " + procedure_item['doctor_data']['user']['first_name'] if \
                            procedure_item['doctor'] else ""
                        invoice_items += item_name + doctor_name + ", "
                    for inventory_item in invoice['invoice']['inventory']:
                        item_name = inventory_item["name"]
                        doctor_name = " By Dr. " + inventory_item['doctor_data']['user']['first_name'] if \
                            inventory_item['doctor'] else ""
                        invoice_items += item_name + doctor_name + ", "
                    invoice['invoice_items'] = invoice_items[0:len(invoice_items) - 2] if len(
                        invoice_items) > 0 else invoice_items
                    invoice['inv_id'] = invoice['invoice']['id']
                    invoice['invoice'] = invoice['invoice']['invoice_id']
            if mail_to:
                for index, item in enumerate(result):
                    invoice_ids = ""
                    items = ""
                    total = 0
                    advance = item["advance_value"] if item["advance_value"] else 0
                    fee = item["payment_mode_data"]["fee"] if item["payment_mode_data"] else 0
                    for i, invoice in enumerate(item['invoices']):
                        invoice_ids += invoice["invoice"]
                        items += invoice['invoice_items']
                        total += invoice["pay_amount"]
                        if i < len(item['invoices']) - 1:
                            invoice_ids += ", "
                            items += ", "
                    ready_data.append({
                        "S. No.": index + 1,
                        "Date": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if 'date' in item else '--',
                        "Patient Id": item["patient"]["custom_id"] if "patient" in item and "custom_id" in item[
                            "patient"] else "--",
                        "Patient Name": item["patient"]["user"]["first_name"] if "patient" in item else "--",
                        "Receipt Number": item["payment_id"] if "payment_id" in item else "--",
                        "Invoice(s)": invoice_ids,
                        "Treatments & Products": items,
                        "Amount Paid (INR)": total,
                        "Advance Amount (INR)": advance,
                        "Payment Info": item["payment_mode_data"]["mode"] if item["payment_mode_data"] else "--",
                        "Vendor Fees": round((total + advance) * fee / 100, 2)
                    })
                subject = "All Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the All Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "All_Payment_Report_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "PATIENT_GROUPS":
            filter_data = {}
            data = []
            for item in queryset:
                patient_id = item.patient.pk if item.patient else None
                if patient_id:
                    patient = Patients.objects.get(id=patient_id)
                    patient_groups = patient.patient_group.all()
                    if len(patient_groups) > 0:
                        amount = 0
                        for invoice in item.invoices.all():
                            amount += invoice.pay_amount
                    for group in patient_groups:
                        if group.id in filter_data:
                            filter_data[group.id]["amount"] += amount
                        else:
                            filter_data[group.id] = {"amount": amount, "name": group.name}
            keys = list(filter_data.keys())
            for patient_groups in keys:
                data.append({"group_id": patient_groups, **filter_data[patient_groups]})
            data = sorted(data, key=lambda x: x["amount"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "Sno": index + 1,
                        "Patient Group": item["name"],
                        "Total Payment (INR)": item["amount"]
                    })
                subject = "Patient Group Wise Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Patient Group Wise Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Group_Wise_Payment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        elif report_type == "UNSETTLED_ADVANCE":
            queryset = queryset.filter(is_advance=True, advance_value__gt=0)
            patients = queryset.order_by('patient').values_list('patient', flat=True).distinct()
            data = []
            for patient in patients:
                patient_obj = Patients.objects.filter(id=patient).first()
                invoices = PatientInvoices.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                          practice=practice_id)
                payments = PatientPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                         practice=practice_id).order_by("date")
                returns = ReturnPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                       practice=practice_id)
                practice_total = 0.0
                unsettled_advance = 0.0
                pay_total = 0.0
                advance = 0.0
                last_date = None
                for invoice in invoices:
                    if invoice.total:
                        practice_total += invoice.total
                for payment in payments:
                    last_date = payment.date
                    pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                    advance = payment.advance_value if payment.advance_value else 0
                    if not payment.return_pay:
                        unsettled_advance += advance
                        practice_total -= (pay_total + advance)
                for return_pay in returns:
                    cash = return_pay.cash_return if return_pay.cash_return else 0
                    practice_total += cash
                    if not return_pay.with_tax:
                        practice_total += return_pay.taxes if return_pay.with_tax else 0
                data.append({
                    "id": patient,
                    "name": patient_obj.user.first_name,
                    "custom_id": patient_obj.custom_id,
                    "advance": unsettled_advance,
                    "net": round(practice_total, 2),
                    "last_payment": pay_total + advance,
                    "payment_date": last_date
                })
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "Sno": index + 1,
                        "Patient Name": item["name"],
                        "Patient Id": item["custom_id"],
                        "Unsettled Advance (INR)": item["advance"],
                        "Net Advance/Due (INR)": item["net"],
                        "Last Payment (INR)": item["last_payment"],
                        "Last Payment On": item["payment_date"].strftime("%d/%m/%Y") if item["payment_date"] else "--"
                    })
                subject = "Unsettled Advance Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Unsettled Advance Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Unsettled_Advance_Payment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        elif report_type == "MODE_OF_PAYMENTS":
            filter_data = {}
            mode_data = {}
            fee_data = {}
            data = []
            for payment in queryset:
                pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                advance = payment.advance_value if payment.advance_value else 0
                payment_mode = payment.payment_mode.pk if payment.payment_mode else -1
                mode_name = payment.payment_mode.mode if payment.payment_mode else "No Payment Mode Defined"
                fee = payment.payment_mode.fee if payment.payment_mode else 0
                total = 0
                if not payment.return_pay:
                    total = (pay_total + advance)
                if payment_mode in filter_data:
                    filter_data[payment_mode] += total
                else:
                    filter_data[payment_mode] = total
                    mode_data[payment_mode] = mode_name
                    fee_data[payment_mode] = fee
            for key in filter_data.keys():
                data.append({"mode": key, "mode_name": mode_data[key], "amount": filter_data[key],
                             "fee_percent": fee_data[key]})
            data = sorted(data, key=lambda x: x["amount"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    fees = round(item["amount"] * item["fee_percent"] / 100, 2)
                    ready_data.append({
                        "Sno": index + 1,
                        "Payment Vendor": item["mode_name"],
                        "Total Payment (INR)": item["amount"],
                        "Vendor Fee": fees,
                        "Net Payment": item["amount"] - fees
                    })
                subject = "Payment Mode Wise Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Payment Mode Wise Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Payment_Mode_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        elif report_type == "DAILY":
            filter_data = {}
            data = []
            for payment in queryset:
                pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                advance = payment.advance_value if payment.advance_value else 0
                pay_date = payment.date if payment.date else datetime.date()
                total = 0
                if not payment.return_pay:
                    total = (pay_total + advance)
                if pay_date in filter_data:
                    filter_data[pay_date] += total
                else:
                    filter_data[pay_date] = total
            for key in filter_data.keys():
                data.append({"date": key, "amount": filter_data[key]})
            data = sorted(data, key=lambda x: x["date"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "Sno": index + 1,
                        "Date": item["date"].strftime("%d/%m/%Y"),
                        "Total Payment (INR)": round(item["amount"], 2)
                    })
                subject = "Daily Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Daily Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Payment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        elif report_type == "MONTHLY":
            filter_data = {}
            data = []
            for payment in queryset:
                pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                advance = payment.advance_value if payment.advance_value else 0
                pay_date = payment.date.replace(day=1) if payment.date else datetime.date().replace(day=1)
                total = 0
                if not payment.return_pay:
                    total = (pay_total + advance)
                if pay_date in filter_data:
                    filter_data[pay_date] += total
                else:
                    filter_data[pay_date] = total
            for key in filter_data.keys():
                data.append({"date": key, "amount": filter_data[key]})
            data = sorted(data, key=lambda x: x["date"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "Sno": index + 1,
                        "Date": item["date"].strftime("%B %Y"),
                        "Total Payment (INR)": round(item["amount"], 2)
                    })
                subject = "Monthly Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Monthly Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Payment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        elif report_type == "DOCTOR":
            result = PatientPaymentDataSerializer(queryset, many=True).data
            filter_data = {}
            doctor_data = {}
            data = []
            for item in result:
                for invoice in item['invoices']:
                    for procedure_item in invoice['invoice']['procedure']:
                        total = procedure_item["total"]
                        doctor_name = procedure_item['doctor_data']['user']['first_name'] if procedure_item['doctor'] \
                            else "No Doctor Assigned"
                        doctor = procedure_item['doctor'] if procedure_item['doctor'] else -1
                        if doctor in filter_data:
                            filter_data[doctor] += total
                        else:
                            filter_data[doctor] = total
                            doctor_data[doctor] = doctor_name
                    for inventory_item in invoice['invoice']['inventory']:
                        total = inventory_item["total"]
                        doctor_name = inventory_item['doctor_data']['user']['first_name'] if inventory_item['doctor'] \
                            else "No Doctor Assigned"
                        doctor = inventory_item['doctor'] if inventory_item['doctor'] else -1
                        if doctor in filter_data:
                            filter_data[doctor] += total
                        else:
                            filter_data[doctor] = total
                            doctor_data[doctor] = doctor_name
            for key in filter_data.keys():
                data.append({"doctor": key, "amount": filter_data[key], "doctor_name": doctor_data[key]})
            data = sorted(data, key=lambda x: x["amount"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "Sno": index + 1,
                        "Doctor Name": item["doctor_name"],
                        "Total Payment (INR)": round(item["amount"], 2)
                    })
                subject = "Doctor Wise Payment Report from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Doctor Wise Payment Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Doctor_Wise_Payment_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})


class PatientWalletViewSet(ModelViewSet):
    serializer_class = PatientWalletSerializer
    queryset = PatientWallet.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(PatientWalletViewSet, self).get_queryset()
        patient = self.request.query_params.get("patient", None)
        if patient:
            queryset = queryset.filter(patient=patient)
        return queryset


class PatientWalletLedgerViewSet(ModelViewSet):
    serializer_class = PatientWalletLedgerSerializer
    queryset = PatientWalletLedger.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientWalletLedgerViewSet, self).get_queryset()
        patient = self.request.query_params.get("patient", None)
        practice = self.request.query_params.get("practice", None)
        agents = self.request.query_params.get("agents", None)
        start = self.request.query_params.get("start", None)
        end = self.request.query_params.get("end", None)
        sort = self.request.query_params.get("sort", None)
        ledger_type = self.request.query_params.get("ledger_type", None)
        queryset = queryset.filter(is_cancelled=False)
        if patient:
            queryset = queryset.filter(patient=patient)
        if practice:
            queryset = queryset.filter(practice=practice)
        if ledger_type:
            queryset = queryset.filter(ledger_type=ledger_type)
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if agents:
            agent_list = agents.split(",")
            user_ids = Patients.objects.filter(id__in=agent_list).values_list('user', flat=True)
            queryset = queryset.filter(invoice__patient__in=agent_list) | queryset.filter(
                invoice__patient__user__in=user_ids)
        if sort:
            queryset = queryset.order_by(sort)
        return queryset

    @action(methods=['GET'], detail=False)
    def export(self, request):
        queryset = PatientWalletLedger.objects.filter(is_cancelled=False)
        patient = request.query_params.get("patient", None)
        practice = request.query_params.get("practice", None)
        agents = request.query_params.get("agents", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        if patient:
            queryset = queryset.filter(patient=patient)
        if practice:
            queryset = queryset.filter(practice=practice)
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if agents:
            agent_list = agents.split(",")
            user_ids = Patients.objects.filter(id__in=agent_list).values_list('user', flat=True)
            queryset = queryset.filter(invoice__patient__in=agent_list) | queryset.filter(
                invoice__patient__user__in=user_ids)
        wallet_ledger = PatientWalletLedgerSerializer(queryset, many=True).data
        data = [["Date", "Time", "Patient", "Referred By", "Ledger Comment", "CR/DR", "Amount"]]
        for item in wallet_ledger:
            referred_by = item['received_from']['user']['referer_data']['referer']['first_name'] + ' (' + \
                          item['received_from']['custom_id'] + ')' if item['received_from'] and \
                                                                      item['received_from']['user']['referer_data'][
                                                                          'referer'] else "--"
            patient_name = item['received_from']['user']['first_name'] if item['received_from'] else "--"
            created_at = pd.to_datetime(item["created_at"])
            items = [created_at.strftime("%d-%m-%Y"), created_at.strftime("%H:%M:%S"), patient_name, referred_by,
                     item['comments'], item['ledger_type'], item["amount"]]
            data.append(items)
        report_name = "Report_PatientWalletLedger" + "_" + str(datetime.now())
        report_path = os.path.join(settings.MEDIA_ROOT, report_name + ".csv")
        with open(report_path, 'w') as csv_file:
            csvwriter = csv.writer(csv_file)
            csvwriter.writerows(data)
        csv_data = File(open(report_path, 'rb'))
        pdf_obj, flag = InventoryCsvReports.objects.get_or_create(inventory=report_name)
        pdf_obj.report_csv.save("%s.csv" % report_name, csv_data)
        html_file = report_path[:-3] + 'html'
        df = pd.read_csv(report_path, sep=',', keep_default_na=False)
        df.index += 1
        df.to_html(html_file)
        html_data = Template(
            open(html_file, "r").read() + "<style>.dataframe {text-align:center;padding: 5px 0;}</style>")
        pdf_content = pdf_document.html_to_pdf_convert(html_data, Context({}))
        pdf_obj.report_pdf.save("%s.pdf" % report_name, pdf_content)
        os.remove(html_file)
        os.remove(report_path)
        return response.Ok(InventoryCsvReportsSerializer(pdf_obj).data)

    @action(methods=['GET'], detail=False)
    def ledger_sum(self, request, *args, **kwargs):
        queryset = PatientWalletLedger.objects.filter(is_cancelled=False)
        patient = request.query_params.get("patient", None)
        practice = request.query_params.get("practice", None)
        agents = request.query_params.get("agents", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        if patient:
            queryset = queryset.filter(patient=patient)
        if practice:
            queryset = queryset.filter(practice=practice)
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if agents:
            agent_list = agents.split(",")
            user_ids = Patients.objects.filter(id__in=agent_list).values_list('user', flat=True)
            queryset = queryset.filter(invoice__patient__in=agent_list) | queryset.filter(
                invoice__patient__user__in=user_ids)
        credit = queryset.filter(ledger_type='Credit').values('amount').aggregate(total=Sum('amount'))
        debit = queryset.filter(ledger_type='Debit').values('amount').aggregate(total=Sum('amount'))
        payout = queryset.filter(ledger_type='Payout').values('amount').aggregate(total=Sum('amount'))
        return response.Ok({"credit": credit["total"] if credit["total"] else 0,
                            "debit": debit["total"] if debit["total"] else 0,
                            "payout": payout["total"] if payout["total"] else 0})

    @action(methods=['GET'], detail=False)
    def top_advisor(self, request, *args, **kwargs):
        queryset = PatientWalletLedger.objects.exclude(ledger_type="Payout").filter(is_cancelled=False)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        patient = request.query_params.get("patient", None)
        agent_id = request.query_params.get("agent_id", None)
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if agent_id:
            queryset = queryset.filter(patient=agent_id)
        if patient:
            queryset = queryset.filter(patient=patient)
        rows = []
        for row in queryset:
            mlm = row.mlm
            ledger_patients = list(PatientWalletLedger.objects.exclude(patient=row.patient) \
                                   .filter(mlm=mlm, is_cancelled=False) \
                                   .values('patient', 'patient__user__referer').distinct())
            for ledger in ledger_patients:
                if ledger['patient__user__referer'] == row.patient.user:
                    if row.ledger_type == "Credit":
                        rows.append({"agent_id": ledger['patient'], "amount": row.amount if row.amount else 0})
                        break
                    elif row.ledger_type == "Debit":
                        rows.append(
                            {"agent_id": ledger['patient'], "amount": row.amount * -1 if row.amount else 0})
                        break
            else:
                if row.invoice.patient != row.patient:
                    if row.ledger_type == "Credit":
                        rows.append({"agent_id": row.invoice.patient.pk, "amount": row.amount if row.amount else 0})
                    elif row.ledger_type == "Debit":
                        rows.append(
                            {"agent_id": row.invoice.patient.pk, "amount": row.amount * -1 if row.amount else 0})
        output = []
        rows.sort(key=lambda x: x["agent_id"])
        for k, v in groupby(rows, key=lambda x: x['agent_id']):
            total = 0
            for item in list(v):
                patient = item["agent_id"]
                total += item["amount"]
            if total > 0:
                output.append({"advisor": PatientsBasicDataSerializer(Patients.objects.get(id=patient)).data,
                               "total": round(total, 2)})
        output.sort(key=lambda x: x["total"], reverse=True)
        return response.Ok(output[0:5])


class ReturnPaymentViewSet(ModelViewSet):
    serializer_class = ReturnPaymentSerializer
    queryset = ReturnPayment.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(ReturnPaymentViewSet, self).get_queryset()
        patient_id = self.request.query_params.get('patient', None)
        practice_id = self.request.query_params.get('practice', None)
        queryset = queryset.filter(is_active=True)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        if practice_id:
            queryset = queryset.filter(practice__id=practice_id)
            practice = Practice.objects.get(id=practice_id)
            hide_cancelled = practice.hide_cancelled_return
            if hide_cancelled:
                queryset = queryset.exclude(is_cancelled=True)
        return queryset.order_by('-date', '-id')

    @action(methods=['GET'], detail=False)
    def update_id(self, request, *args, **kwargs):
        queryset = ReturnPayment.objects.all().order_by("id")
        for obj in queryset:
            prefix = obj.practice.return_prefix if obj and obj.practice and obj.practice.return_prefix else ""
            return_id = prefix + str(ReturnPayment.objects.filter(practice=obj.practice, id__lte=obj.pk).count())
            ReturnPayment.objects.filter(id=obj.pk).update(return_id=return_id)
        return response.Ok({"detail": "Updated"})

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def return_reports(self, request, *args, **kwargs):
        practice_id = request.query_params.get('practice', None)
        is_cancelled = request.query_params.get('is_cancelled', None)
        income_type = request.query_params.get('income_type', None)
        report_type = request.query_params.get('type', None)
        doctors = request.query_params.get('doctors', None)
        groups = request.query_params.get('groups', None)
        treatments = request.query_params.get('treatments', None)
        products = request.query_params.get('products', None)
        taxes = request.query_params.get('taxes', None)
        discount = request.query_params.get('discount', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        mail_to = request.query_params.get('mail_to', None)
        queryset = ReturnPayment.objects.filter(is_active=True)
        practice_name = CONST_GLOBAL_PRACTICE
        start_date = end_date = datetime.today().date()
        ready_data = []
        if practice_id:
            queryset = queryset.filter(practice=practice_id)
            instance = Practice.objects.filter(id=practice_id).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if is_cancelled:
            is_cancelled = True if is_cancelled == "true" else False
            queryset = queryset.filter(is_cancelled=is_cancelled)
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(inventory__doctor__in=doctor_list) | queryset.filter(
                procedure__doctor__in=doctor_list)
        if groups:
            group_list = groups.split(",")
            patients = Patients.objects.filter(patient_group__in=group_list).values_list('id', flat=True)
            queryset = queryset.filter(patient__in=patients)
        if treatments:
            treatment_list = treatments.split(",")
            queryset = queryset.filter(procedure__procedure__in=treatment_list)
        if products:
            product_list = products.split(",")
            queryset = queryset.filter(inventory__inventory__in=product_list)
        if taxes:
            tax_list = taxes.split(",")
            queryset = queryset.filter(procedure__taxes__in=tax_list) | queryset.filter(inventory__taxes__in=tax_list)
        if discount and discount == "ZERO":
            queryset = queryset.filter(procedure__discount_value__lt=1) | queryset.filter(
                inventory__discount_value__lt=1)
        elif discount and discount == "NON_ZERO":
            queryset = queryset.filter(procedure__discount_value__gt=1) | queryset.filter(
                inventory__discount_value__gt=1)
        if start and end:
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            queryset = queryset.filter(date__range=[start_date, end_date])
        if income_type and income_type == "PRODUCTS":
            queryset = queryset.exclude(inventory=None)
        elif income_type and income_type == "SERVICES":
            queryset = queryset.exclude(procedure=None)
        queryset = queryset.distinct()
        if report_type == "ALL":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            if mail_to:
                for index, item in enumerate(res):
                    treatments = ""
                    for procedure in item["procedure"]:
                        treatments += procedure["name"] + "," if "name" in procedure else ""
                    for inventory in item["inventory"]:
                        treatments += inventory["name"] + "," if "name" in inventory else ""
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Date": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if item['date'] else "--",
                        "Return Number": item["return_id"],
                        "Patient Name": item["patient_data"]["user"]["first_name"] if "patient_data" in item else "--",
                        "Patient ID": item["patient_data"]["custom_id"] if "patient_data" in item else "--",
                        "Treatment & Products": treatments,
                    })
                subject = "Return Invoice Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Income_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                res = {"detail": msg, "error": error}
            if "error" in res and res["error"]:
                return response.BadRequest(res)
            return response.Ok(res)
        if report_type == "DAILY":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                value = self.calculate_total(item)
                if item["date"] and item["date"] in filter_data:
                    filter_data[item["date"]]["cost"] += value["cost"]
                    filter_data[item["date"]]["tax"] += value["tax"]
                    filter_data[item["date"]]["discount"] += value["discount"]
                elif item["date"]:
                    filter_data[item["date"]] = value
            keys = list(filter_data.keys())
            keys.sort()
            for date in keys:
                data.append({"date": date, **filter_data[date]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Day": pd.to_datetime(item["date"]).strftime("%d/%m/%Y") if item['date'] else "--",
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Daily Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Return_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "MONTHLY":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                value = self.calculate_total(item)
                item_date = item["date"][:-3] if item["date"] else "NA"
                if item_date in filter_data:
                    filter_data[item_date]["cost"] += value["cost"]
                    filter_data[item_date]["tax"] += value["tax"]
                    filter_data[item_date]["discount"] += value["discount"]
                else:
                    filter_data[item_date] = value
            keys = list(filter_data.keys())
            keys.sort()
            for date in keys:
                data.append({"date": date + "-01", **filter_data[date]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Day": pd.to_datetime(item["date"]).strftime("%B %Y") if item['date'] else "--",
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Monthly Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Return_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "TAX":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    total_tax = 0
                    for tax in inv["taxes_data"]:
                        total_tax += tax["tax_value"]
                    for tax in inv["taxes_data"]:
                        if tax["id"] in filter_data:
                            filter_data[tax["id"]]["total"] += inv["tax_value"] * tax["tax_value"] / total_tax
                        else:
                            filter_data[tax["id"]] = {"name": tax["name"], "tax_value": tax["tax_value"],
                                                      "total": inv["tax_value"] * tax["tax_value"] / total_tax}
                for procedure in item["procedure"]:
                    total_tax = 0
                    for tax in procedure["taxes_data"]:
                        total_tax += tax["tax_value"]
                    for tax in procedure["taxes_data"]:
                        if tax["id"] in filter_data:
                            filter_data[tax["id"]]["total"] += inv["tax_value"] * tax["tax_value"] / total_tax
                        else:
                            filter_data[tax["id"]] = {"name": tax["name"], "tax_value": tax["tax_value"],
                                                      "total": inv["tax_value"] * tax["tax_value"] / total_tax}
            keys = list(filter_data.keys())
            keys.sort()
            for tax_id in keys:
                data.append({"id": tax_id, **filter_data[tax_id]})
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No.": index + 1,
                        "Tax Name": item["name"] if item['name'] else "--",
                        "Tax Value": str(item["tax_value"]) + "%" if item['tax_value'] else "--",
                        "Tax(INR)": round(item["total"], 2)
                    })
                subject = "Tax Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Tax_Return_Report_" + start + "_" + end, mail_to, subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)

            return response.Ok(data)
        if report_type == "DOCTOR":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    doctor_id = str(inv["doctor"]) if inv["doctor"] else "NA"
                    if doctor_id in filter_data:
                        filter_data[doctor_id]["cost"] += inv["total"] - inv["tax_value"]
                        filter_data[doctor_id]["discount_value"] += inv["discount_value"]
                        filter_data[doctor_id]["tax_value"] += inv["tax_value"]
                    else:
                        filter_data[doctor_id] = {"cost": inv["total"] - inv["tax_value"],
                                                  "discount_value": inv["discount_value"],
                                                  "tax_value": inv["tax_value"]}
                for procedure in item["procedure"]:
                    doctor_id = str(procedure["doctor"]) if procedure["doctor"] else "NA"
                    if doctor_id in filter_data:
                        filter_data[doctor_id]["cost"] += procedure["total"] - procedure["tax_value"]
                        filter_data[doctor_id]["discount_value"] += procedure["discount_value"]
                        filter_data[doctor_id]["tax_value"] += procedure["tax_value"]
                    else:
                        filter_data[doctor_id] = {"cost": procedure["total"] - procedure["tax_value"],
                                                  "discount_value": procedure["discount_value"],
                                                  "tax_value": procedure["tax_value"]}
            keys = list(filter_data.keys())
            keys.sort()
            for doctor in keys:
                data.append({"doctor": doctor, **filter_data[doctor]})
            if mail_to:
                for index, item in enumerate(data):
                    doctor_name = PracticeStaff.objects.filter(id=item["doctor"]).first().user.first_name
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Doctor": doctor_name,
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Doctor Wise Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Doctor_Wise_Return_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PROCEDURE":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, "SERVICES", doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for procedure in item["procedure"]:
                    procedure_id = procedure["procedure"] if procedure["procedure"] else "NA"
                    if procedure_id in filter_data:
                        filter_data[procedure_id]["cost"] += procedure["total"] - procedure["tax_value"]
                        filter_data[procedure_id]["discount_value"] += procedure["discount_value"]
                        filter_data[procedure_id]["tax_value"] += procedure["tax_value"]
                    else:
                        filter_data[procedure_id] = {"cost": procedure["total"] - procedure["tax_value"],
                                                     "discount_value": procedure["discount_value"],
                                                     "tax_value": procedure["tax_value"],
                                                     "name": procedure["name"]}
            keys = list(filter_data.keys())
            for procedure in keys:
                data.append({"procedure": procedure, **filter_data[procedure]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Treatment Category": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Procedure Wise Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Procedure_Wise_Return_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PRODUCT":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, "PRODUCTS", doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                for inv in item["inventory"]:
                    inv_id = inv["inventory"] if inv["inventory"] else "NA"
                    if inv_id in filter_data:
                        filter_data[inv_id]["cost"] += inv["total"] - inv["tax_value"]
                        filter_data[inv_id]["discount_value"] += inv["discount_value"]
                        filter_data[inv_id]["tax_value"] += inv["tax_value"]
                    else:
                        filter_data[inv_id] = {"cost": inv["total"] - inv["tax_value"],
                                               "discount_value": inv["discount_value"],
                                               "tax_value": inv["tax_value"],
                                               "name": inv["name"]}
            keys = list(filter_data.keys())
            for product in keys:
                data.append({"product": product, **filter_data[product]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Product Name": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount_value"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2),
                        "Tax(INR)": round(item["tax_value"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount_value"], 2) - round(
                            item["tax_value"], 2),
                    })
                subject = "Product Wise Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Product_Wise_Return_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        if report_type == "PATIENT_GROUPS":
            data = ReturnPaymentSerializer(queryset, many=True).data
            res = self.data_filter(data, income_type, doctors, treatments, products, taxes, discount)
            data = []
            filter_data = {}
            for item in res:
                patient_id = item["patient"] if item["patient"] else None
                if patient_id:
                    patient = Patients.objects.get(id=patient_id)
                    patient_groups = patient.patient_group.all()
                    if len(patient_groups) > 0:
                        value = self.calculate_total(item)
                    for group in patient_groups:
                        if group in filter_data:
                            filter_data[group.id]["cost"] += value["cost"]
                            filter_data[group.id]["discount_value"] += value["discount_value"]
                            filter_data[group.id]["tax_value"] += value["tax_value"]
                        else:
                            filter_data[group.id] = value
                            filter_data[group.id]["name"] = group.name
            keys = list(filter_data.keys())
            for patient_groups in keys:
                data.append({"group_id": patient_groups, **filter_data[patient_groups]})
            data = sorted(data, key=lambda x: x["cost"], reverse=True)
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S.No. ": index + 1,
                        "Patient Group": item["name"],
                        "Cost(INR)": round(item["cost"], 2),
                        "Discount(INR)": round(item["discount"], 2),
                        "Return after Discount(INR)": round(item["cost"], 2) - round(item["discount"], 2),
                        "Tax(INR)": round(item["tax"], 2),
                        "Return Amount(INR)": round(item["cost"], 2) - round(item["discount"], 2) - round(item["tax"],
                                                                                                          2),
                    })
                subject = "Patient Group Return Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Group_Return_Report_" + start + "_" + end, mail_to,
                                          subject,
                                          body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)

            return response.Ok(data)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})

    def calculate_total(self, data):
        total = 0
        tax_value = 0
        discount_value = 0
        for inv in data["inventory"]:
            total += inv["total"]
            discount_value += inv["discount_value"]
            tax_value += inv["tax_value"]
        for procedure in data["procedure"]:
            total += procedure["total"]
            discount_value += procedure["discount_value"]
            tax_value += procedure["tax_value"]
        # if data["reservation"]:
        #     total += data["total"] if "total" in data and data["total"] else 0
        #     discount_value += data["discount"] if "discount" in data and data["discount"] else 0
        #     tax_value += data["taxes"] if "taxes" in data and data["taxes"] else 0
        return {"cost": total - tax_value, "tax": tax_value, "discount": discount_value}

    def data_filter(self, data, income_type, doctors, treatments, products, taxes, discount):
        res = []
        for item in data:
            if income_type and income_type == "PRODUCTS":
                item["procedure"] = []
            elif income_type and income_type == "SERVICES":
                item["inventory"] = []
            if doctors:
                doctor_list = doctors.split(",")
                doctor_list = list(map(int, doctor_list))
                inv_items = []
                for inv in item["inventory"]:
                    if inv["doctor"] in doctor_list:
                        inv_items.append(inv)
                item["inventory"] = inv_items
                procedure_items = []
                for procedure in item["procedure"]:
                    if procedure["doctor"] in treatment_list:
                        procedure_items.append(procedure)
                item["procedure"] = procedure_items
            if products:
                product_list = products.split(",")
                product_list = list(map(int, product_list))
                inv_items = []
                for inv in item["inventory"]:
                    if inv["inventory"] in product_list:
                        inv_items.append(inv)
                item["inventory"] = inv_items
            if treatments:
                treatment_list = treatments.split(",")
                treatment_list = list(map(int, treatment_list))
                procedure_items = []
                for procedure in item["procedure"]:
                    if procedure["procedure"] in treatment_list:
                        procedure_items.append(procedure)
                item["procedure"] = procedure_items
            if taxes:
                tax_list = taxes.split(",")
                tax_list = list(map(int, tax_list))
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if len(list(set(inv["taxes"]).intersection(tax_list))) != 0:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if len(list(set(procedure["taxes"]).intersection(tax_list))) != 0:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            if discount and discount == "ZERO":
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if inv["discount_value"] < 1:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if procedure["discount_value"] < 1:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            elif discount and discount == "NON_ZERO":
                inv_items = []
                procedure_items = []
                for inv in item["inventory"]:
                    if inv["discount_value"] >= 1:
                        inv_items.append(inv)
                for procedure in item["procedure"]:
                    if procedure["discount_value"] >= 1:
                        procedure_items.append(procedure)
                item["inventory"] = inv_items
                item["procedure"] = procedure_items
            if len(item["inventory"]) != 0 or len(item["procedure"]) != 0:
                res.append(item)
        return res

    @action(methods=['GET'], detail=True)
    def get_pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        patient_name = instance.patient.user.first_name if instance.patient and instance.patient.user else "User"
        mail_to = request.query_params.get("mail_to", None)
        practice = instance.practice.pk if instance.practice else None
        patient = instance.patient.pk if instance.patient else None
        pdf_obj = generate_pdf("BILLING", "RETURN", ReturnPayment, ReturnPaymentSerializer, instance.pk,
                               practice, patient, None, "return.html", "ReturnId")
        result = GeneratedPdfSerializer(pdf_obj).data
        if mail_to:
            result = mail_file(patient_name, mail_to, pdf_obj, practice, "Return")
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)


class PatientsPromoCodeViewSet(ModelViewSet):
    serializer_class = PatientsPromoCodeSerializer
    queryset = PatientsPromoCode.objects.all()
    permission_classes = (BillingPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientsPromoCodeViewSet, self).get_queryset()
        patient_id = self.request.query_params.get('patient', None)
        practice_id = self.request.query_params.get('practice', None)
        promo_code = self.request.query_params.get('promo_code', None)
        queryset = queryset.filter(is_active=True, expiry_date__gte=datetime.now())
        if patient_id:
            queryset = queryset.filter(patients=patient_id) | queryset.filter(patients=None)
        if practice_id:
            queryset = queryset.filter(practice=practice_id)
        if promo_code:
            queryset = queryset.filter(promo_code=promo_code)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=True)
    def promo_code_sms(self, request, *args, **kwargs):
        result = sms.prepare_promo_code_sms(self.get_object())
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET'], detail=False)
    def promo_value(self, request, *args, **kwargs):
        patient_id = request.query_params.get('patient', None)
        practice_id = request.query_params.get('practice', None)
        promo_code = request.query_params.get('promo_code', None)
        amount = request.query_params.get('amount', None)
        error = True
        discount = 0
        if patient_id and practice_id and promo_code and amount:
            queryset = PatientsPromoCode.objects.filter(promo_code=promo_code, is_active=True,
                                                        practice=practice_id).first()
            if queryset:
                if queryset.expiry_date.replace(tzinfo=None) < datetime.now():
                    msg = "Promocode Expired"
                elif PatientInvoices.objects.filter(promo_code=promo_code, patient=patient_id, is_active=True).exists():
                    msg = "Promocode already redeemed by this patient"
                elif queryset.minimum_order > float(amount):
                    msg = "Minimum amount for this order should be Rs." + str(queryset.minimum_order)
                else:
                    error = False
                    msg = "Valid Promocode"
                    if queryset.code_type == "%":
                        discount = float(amount) * queryset.code_value / 100
                        if discount > queryset.maximum_discount:
                            discount = queryset.maximum_discount
                    else:
                        discount = queryset.code_value
                if len(queryset.patients.all()) != 0:
                    for patient in queryset.patients.all():
                        if int(patient.pk) == int(patient_id):
                            break
                    else:
                        error = True
                        msg = "Promocode not valid for this patient"
            elif PatientsPromoCode.objects.filter(promo_code=promo_code, is_active=True).exists():
                msg = "Promocode is not valid on this Clinic"
            else:
                msg = "Invalid Promocode"
            if error:
                return response.BadRequest({"detail": msg})
            else:
                return response.Ok({"detail": msg, "discount": discount})
        else:
            return response.BadRequest({"detail": "Please send Practice, Patient, Promo code and Invoiceamount"})
