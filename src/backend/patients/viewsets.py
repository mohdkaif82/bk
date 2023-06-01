from __future__ import unicode_literals

import base64
import os
import random
import string
from datetime import timedelta, date, datetime
import pandas as pd
import xmltodict
from ..accounts.models import User
from ..appointment.models import Appointment
from ..blog.models import *
from ..blog.serializers import *
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..billing.serializers import ReturnPaymentSerializer, PatientPaymentSerializer, PatientPaymentDataSerializer, \
    PatientInvoicesDataSerializer, PatientWalletLedgerDataSerializer, PatientWalletDataSerializer
from ..constants import CONST_CANCELLED, CONST_GLOBAL_PRACTICE, CONST_PATIENT_DATA, CONST_DOCTOR_DATA, \
    CONST_MEDICAL_LEAVE_DATA, CONST_VITAL_SIGN_DATA, CONST_CLINICAL_NOTES_DATA, CONST_TREATMENT_PLAN_DATA, \
    CONST_PRESCRIPTION_DATA, CONST_PAYMENTS_DATA, CONST_RETURN_DATA, CONST_INVOICE_DATA, CONST_LAB_ORDER_DATA, \
    CONST_CASE_SHEET_DATA, CONST_MEMBERSHIP, CONST_BOOKING_DATA, CONST_PRACTICE_DATA, CONST_APPOINTMENT_DATA, \
    CONST_REGISTRATION
from ..inventory.models import InventoryItem
from ..inventory.serializers import InventoryItemSerializer
from ..muster_roll.services import create_update_multiple_record
from .models import Patients, PatientGroups, PatientMedicalHistory, ReturnPayment, Source, \
    PatientMembership, PatientVitalSigns, PatientClinicNotes, PatientTreatmentPlans, PatientFile, RequestOTP, \
    PatientPrescriptions, PatientInvoices, PatientPayment, Country, State, City, PatientProcedure, PatientNotes, \
    MedicalCertificate, PatientWallet, GeneratedPdf, PatientWalletLedger, Reservations, PatientCallNotes, \
    PersonalDoctorsPractice, ColdCalling, PatientAllopathicMedicines, PatientRegistration, AdvisorBank,\
    Service,PatientManualReport
from .permissions import PatientsPermissions
from ..blog.permissions import BlogImagePermissions
from .serializers import PatientsSerializer, PatientGroupsSerializer, PatientMedicalHistorySerializer, \
    PatientMembershipSerializer, PatientVitalSignsSerializer, PatientClinicNotesSerializer, PatientFileSerializer, \
    PatientClinicNotesDataSerializer, PatientCallNotesDetailSerializer, GeneratedPdfSerializer, ColdCallingSerializer, \
    PatientCallNotesSerializer, PatientsBasicDataSerializer, PatientPrescriptionsSerializer, ColdCallingDataSerializer, \
    PatientPrescriptionsDataSerializer, PatientProcedureSerializer, PatientProcedureDataSerializer, \
    PatientNotesSerializer, PatientNotesDataSerializer, MedicalCertificateSerializer, PatientMembershipDataSerializer, \
    CountrySerializer, StateSerializer, CitySerializer, PatientsReferalSerializer, PatientMembershipReportSerializer, \
    SourceSerializer, PatientsFollowUpSerializer, PatientsPersonalDoctorsPracticeSerializer, PatientInventorySerializer, \
    PatientAllopathicMedicinesSerializer, PatientRegistrationSerializer, PatientRegistrationDataSerializer, \
    AdvisorBankSerializer, AdvisorBankDataSerializer, PatientRegistrationReportSerializer,\
    PatientsDetailsSerializer,ServiceSerializer,PatientManualReportSerializer
from .services import update_pratice_patient_details, update_patient_extra_details, generate_app_report, \
    update_patient_prescriptions, update_patient_procedure, generate_pdf, generate_timeline, common_function, mail_file, \
    create_update_record, get_advisor_sale
from ..practice.models import Practice, PracticeStaff, Membership, Registration
from ..practice.serializers import PracticeSerializer
from ..practice.services import dict_to_mail
from ..utils import timezone, pdf_document
from ..utils.sms import send_sms_without_save
from dateutil.relativedelta import *
from django.conf import settings
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth as Month, TruncYear as Year, TruncDay as Day
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.loader import get_template
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework_xml.parsers import XMLParser

from .crons import appointment_summary


class PatientViewSet(ModelViewSet):
    serializer_class = PatientsSerializer
    queryset = Patients.objects.all()
    permission_classes = (PatientsPermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super(PatientViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        gender = self.request.query_params.get("gender", None)
        age = self.request.query_params.get("age", None)
        type = self.request.query_params.get("type", None)
        group = self.request.query_params.get("group", None)
        agent = self.request.query_params.get("agent", None)
        is_dead = self.request.query_params.get("is_dead", None)
        role = self.request.query_params.get("role", None)
        referred_by = self.request.query_params.get("referred_by", None)
        pagination = self.request.query_params.get("pagination", False)
        approved = self.request.query_params.get("approved", None)
        practice = self.request.query_params.get("practice", None)
        perm_practice = self.request.query_params.get("perm_practice", None)
        name_starts = self.request.query_params.get("name_starts", None)
        name_equals = self.request.query_params.get("name_equals", None)
        pd_doctor = self.request.query_params.get("pd_doctor", None)
        religions = self.request.query_params.get("religions", None)
        medical_history = self.request.query_params.get("medical_history", None)
        if gender:
            queryset = queryset.filter(gender=gender)
        if age:
            diff = date.today() - timedelta(days=365 * int(age))
            if type == 'lt':
                queryset = queryset.filter(dob__gte=diff)
            elif type == 'gt':
                queryset = queryset.filter(dob__lte=diff)
        if group:
            queryset = queryset.filter(patient_group=group)
        if name_starts:
            queryset = queryset.filter(user__first_name__startswith=name_starts)
        if name_equals:
            queryset = queryset.filter(user__first_name=name_equals)
        if agent:
            is_agent = True if agent == 'true' else False
            queryset = queryset.filter(is_agent=is_agent)
        if is_dead:
            is_dead = True if is_dead == 'true' else False
            queryset = queryset.filter(is_dead=is_dead)
        if approved:
            is_approved = True if approved == 'true' else False
            queryset = queryset.filter(is_approved=is_approved)
        if role:
            queryset = queryset.filter(role=role)
        if practice:
            queryset = queryset.filter(practice=practice)
        if perm_practice:
            queryset = queryset.filter(practices__practice=perm_practice)
        if referred_by:
            queryset = queryset.filter(user__referer=referred_by)
        if pd_doctor:
            queryset = queryset.filter(pd_doctor=pd_doctor)
        if medical_history:
            history_list = medical_history.split(",")
            queryset = queryset.filter(medical_history__in=history_list)
        if religions:
            religion_list = religions.split(",")
            queryset = queryset.filter(religion__in=religion_list)
        if pagination:
            pagination = False if pagination == "false" else True
            self.pagination_class = StandardResultsSetPagination if pagination else None
        return queryset.order_by('user__first_name')

    def retrieve(self, request, pk=None):
        queryset = Patients.objects.filter(is_active=True)
        perm_practice = request.query_params.get("perm_practice", None)
        patient = get_object_or_404(queryset, pk=pk)
        serializer_class = PatientsSerializer
        if perm_practice and len(patient.practices.filter(practice=perm_practice)) == 0:
            serializer_class = PatientsPersonalDoctorsPracticeSerializer
        return response.Ok(serializer_class(patient).data)

    def update(self, request, *args, **kwargs):
        user = request.user if request.user and request.user.is_authenticated else None
        staff = PracticeStaff.objects.filter(user=user, is_active=True, user__is_active=True).first() if user else None
        data = request.data.copy()
        source_extra = data.pop('source_extra', None)
        country_extra = data.pop('country_extra', None)
        state_extra = data.pop('state_extra', None)
        city_extra = data.pop('city_extra', None)
        follow_up_date = data.get('follow_up_date', None)
        medicine_till = data.get('medicine_till', None)
        is_agent = data.get('is_agent', None)
        is_approved = data.get('is_approved', None)
        referal = data.pop('referal', None)
        if referal and not User.objects.filter(referer_code=referal).exists():
            return response.BadRequest({"detail": "Invalid Referal Code..!"})
        elif referal:
            user_referer = User.objects.filter(referer_code=referal).first()
        else:
            user_referer = None
        if source_extra:
            data["source"] = Source.objects.create(name=source_extra)
        if country_extra:
            data["country"] = Country.objects.create(name=country_extra)
        if state_extra:
            country_id = data["country"].pk if isinstance(data["country"], Country) else data["country"]
            country_obj = Country.objects.get(id=country_id)
            data["state"] = State.objects.create(name=state_extra, country=country_obj)
        if city_extra:
            state_id = data["state"].pk if isinstance(data["state"], State) else data["state"]
            state_obj = State.objects.get(id=state_id)
            data["city"] = City.objects.create(name=city_extra, state=state_obj)
        medical_history = data.pop('medical_history') if 'medical_history' in data else []
        patient_group = data.pop('patient_group') if 'patient_group' in data else []
        practices = data.pop('practices') if 'practices' in data else []
        queryset = super(PatientViewSet, self).get_queryset()
        queryset = queryset.filter(pk=kwargs.get('pk'))
        if staff and (queryset[0].follow_up_date != follow_up_date or queryset[0].medicine_till != medicine_till):
            data["follow_up_staff"] = staff
        if "custom_id" not in data:
            data["custom_id"] = "BK" + str(queryset[0].pk)
        elif "custom_id" in data and data["custom_id"] is None:
            data["custom_id"] = "BK" + str(queryset[0].pk)
        if "pd_doctor" in data and data["pd_doctor"] and queryset[0].pd_doctor.pk != data["pd_doctor"]:
            data["pd_doctor_added"] = datetime.now()
        if is_agent and is_approved and (queryset[0].is_agent != is_agent or queryset[0].is_approved != is_approved):
            data["advisor_joined"] = datetime.now()
        if 'user' in data:
            user = data.pop('user')
            user_id = queryset.filter(pk=kwargs.get('pk')).values('user').first()['user']
            mobile = user.get('mobile')
            name = user.get('first_name')
            email = user.get('email')
            if not User.objects.filter(mobile=mobile).exclude(id=user_id).exists():
                User.objects.filter(id=user_id).update(first_name=name, email=email, mobile=mobile,
                                                       referer=user_referer)
            else:
                return response.BadRequest({"detail": "This mobile number is associated with another patient."})
        if 'user' in data and not data['user']:
            return response.BadRequest({"detail": "Send User with data."})
        if 'dob' in data and data['dob'] == '':
            data['dob'] = None
        queryset.update(**data)
        queryset[0].medical_history.set(PatientMedicalHistory.objects.filter(id__in=medical_history))
        queryset[0].patient_group.set(PatientGroups.objects.filter(id__in=patient_group))
        pdp = []
        new_practices = []
        for i in range(len(practices)):
            for j in range(i + 1, len(practices)):
                if practices[i]["practice"] == practices[j]["practice"]:
                    break
            else:
                new_practices.append(practices[i])
        for practice_data in new_practices:
            practice_id = practice_data.get("practice", None)
            practice_obj = Practice.objects.get(id=practice_id) if practice_id else None
            pdp.append(PersonalDoctorsPractice.objects.create(practice=practice_obj))
            queryset[0].practices.set(pdp)
        instance = self.queryset.get(pk=kwargs.get('pk'))
        instance.save()
        serializer = self.get_serializer(instance)
        return response.Ok(serializer.data)

    @action(methods=['GET'], detail=True)
    def print_ticket(self, request, *args, **kwargs):
        practice_name = request.query_params.get("name", None)
        practice_address1 = request.query_params.get("address1", None)
        practice_address2 = request.query_params.get("address2", None)
        extra = request.query_params.get("extra", None)
        practice_contact = request.query_params.get("contact", None)
        patient = self.get_object().pk
        extra_data = {
            "name": practice_name,
            "address1": practice_address1,
            "address2": practice_address2,
            "extra": extra,
            "contact": practice_contact
        }
        pdf_obj = generate_pdf("PATIENT PROFILE", "ADDRESS TICKET", None, None, None,
                               None, patient, None, "address_ticket.html", "AddressID", extra_data)
        result = GeneratedPdfSerializer(pdf_obj).data
        return response.Ok(result)

    @action(methods=['POST'], detail=False)
    def bbps_bill(self, request, *args, **kwargs):
        result = xmltodict.parse(request.body.decode("utf-8"))
        res = {
            "code": 200,
            "amount_due": 0,
            "approval_ref": "NA",
            "message": "Incorrect / Invalid customer account"
        }
        if result.get('bbps:BillFetchRequest', None) and result.get('bbps:BillFetchRequest', None) \
                .get('CustomerInput', None) and result.get('bbps:BillFetchRequest', None).get('CustomerInput', None) \
                .get('Tag', None) and result.get('bbps:BillFetchRequest', None).get('CustomerInput', None) \
                .get('Tag', None).get('@value', None):
            mobile = result.get('bbps:BillFetchRequest').get('CustomerInput').get('Tag').get('@value')
            patient_obj = Patients.objects.filter(user__mobile=mobile).order_by('-id').first()
            res["patient"] = patient_obj
            if patient_obj and not patient_obj.is_active:
                res["code"] = 201
                res["message"] = "Customer account is not activated"
            elif patient_obj:
                practices = Practice.objects.filter(is_active=True)
                data = []
                for practice in practices:
                    invoice_title = ""
                    practice_total = 0.0
                    invoices = PatientInvoices.objects.filter(is_cancelled=False, is_active=True, patient=patient_obj,
                                                              practice=practice)
                    payments = PatientPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient_obj,
                                                             practice=practice)
                    returns = ReturnPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient_obj,
                                                           practice=practice)
                    for invoice in invoices:
                        if invoice.total:
                            practice_total += invoice.total
                        if invoice.is_pending:
                            invoice_title += invoice.invoice_id + ", "
                    for payment in payments:
                        if not payment.return_pay:
                            pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                            advance = payment.advance_value if payment.advance_value else 0
                            practice_total -= (pay_total + advance)
                    for return_pay in returns:
                        cash = return_pay.cash_return if return_pay.cash_return else 0
                        practice_total += cash
                        if not return_pay.with_tax:
                            practice_total += return_pay.taxes if return_pay.with_tax else 0
                    data.append({
                        "name": practice.name,
                        "total": round(practice_total, 2),
                        "invoices": invoice_title
                    })
                data = sorted(data, key=lambda i: i["total"], reverse=True)
                if len(data) > 0 and "total" in data[0] and data[0]["total"] > 0:
                    total = data[0]["total"]
                    invoice_names = data[0]["invoices"][:-2] if len(data[0]["invoices"]) > 0 else data[0]["invoices"]
                    res["amount_due"] = total
                    res["invoices"] = invoice_names
                    res["practice_name"] = data[0]["name"]
                    res["code"] = 0
                    res["approval_ref"] = patient_obj.user.mobile
                    res["message"] = "Successful"
                else:
                    res["code"] = 202
                    res["message"] = "Payment received for the billing period - No bill due"
        return render(request, 'bbps_bill.xml', res)

    @action(methods=['POST'], detail=False)
    def bbps_payment(self, request, *args, **kwargs):
        result = xmltodict.parse(request.body.decode("utf-8"))
        res = {
            "code": 200,
            "message": "Incorrect / Invalid customer account",
            "approval_ref": "NA"
        }
        if result.get('bbps:BillPaymentRequest', None) and result.get('bbps:BillPaymentRequest', None) \
                .get('PaymentDetails', None) and result.get('bbps:BillPaymentRequest', None) \
                .get('PaymentDetails', None).get('Txn', None) and result.get('bbps:BillPaymentRequest', None) \
                .get('PaymentDetails', None).get('Txn', None).get('@value', None):
            tags = result.get('bbps:BillPaymentRequest').get('PaymentDetails').get('Tag', [])
            mobile, invoices, remarks, pay_mode, paid, practice = None, "", "BBPS Payment", "", 0.0, 1
            txn_id = result.get('bbps:BillPaymentRequest').get('PaymentDetails').get('Txn').get('@value')
            pay_date = timezone.now_local(True)
            for tag in tags:
                tag_name = tag.get("@name", None)
                tag_value = tag.get("@value", None)
                if tag_name == "billNumber":
                    invoices = tag_value
                elif tag_name == "Payment Date":
                    pay_date = tag_value
                elif tag_name == "Payment Mode":
                    pay_mode = tag_value
                elif tag_name == "Amount Paid":
                    paid = float(tag_value)
                elif tag_name == "Registered Mobile Number":
                    mobile = tag_value
            patient_obj = Patients.objects.filter(user__mobile=mobile).order_by('-id').first()
            res["patient"] = patient_obj
            if not mobile:
                res["code"] = 200
                res["message"] = "Incorrect / Invalid customer account"
            elif patient_obj and not patient_obj.is_active:
                res["code"] = 201
                res["message"] = "Customer account is not activated"
            elif txn_id and PatientPayment.objects.filter(notes__icontains=txn_id, is_cancelled=False,
                                                          is_active=True).exists():
                res["code"] = 204
                res["message"] = "Repeat payment request"
            elif patient_obj:
                invoices_data = []
                for invoice in invoices.split(","):
                    invoice_obj = PatientInvoices.objects.filter(invoice_id=invoice, is_active=True,
                                                                 is_cancelled=False).first()
                    if invoice_obj:
                        practice = invoice_obj.practice.pk
                        invoice_detail = PatientInvoicesDataSerializer(invoice_obj).data
                        invoice_total = invoice_detail["total"] if invoice_detail["total"] else 0
                        payments = invoice_detail["payments_data"] if invoice_detail["payments_data"] else 0
                        pending = invoice_total - payments
                        if pending >= 1:
                            if pending <= paid:
                                invoices_data.append({"invoice": invoice_obj.pk, "pay_amount": pending})
                                paid -= pending
                            else:
                                invoices_data.append({"invoice": invoice_obj.pk, "pay_amount": paid})
                                paid = 0
                                break
                is_advance = True if paid >= 1 else False
                payment_dict = {
                    "patient": patient_obj.pk,
                    "practice": practice,
                    "invoices": invoices_data,
                    "bank": pay_mode,
                    "advance_value": paid if paid >= 1 else 0,
                    "is_advance": is_advance,
                    "date": pay_date,
                    "notes": remarks + " - Txn no: " + txn_id
                }
                pay_serializer = PatientPaymentSerializer(data=payment_dict, partial=True)
                pay_serializer.is_valid(raise_exception=True)
                pay_serializer.save()
                res["code"] = 0
                res["message"] = "Successful"
                res["approval_ref"] = txn_id
        else:
            res["code"] = 203
            res["message"] = "Invalid combination of customer parameters"
        return render(request, 'bbps_payment.xml', res)

    @action(methods=['GET', 'POST'], detail=False)
    def allopath(self, request, *args, **kwargs):
        if request.method == "GET":
            patient = request.query_params.get("patient", None)
            start = request.query_params.get("start", None)
            end = request.query_params.get("end", None)
            queryset = PatientAllopathicMedicines.objects.filter(is_active=True)
            if patient:
                queryset = queryset.filter(patient=patient)
            if start and end:
                queryset = queryset.filter(start__lte=end, end__gte=start)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(PatientAllopathicMedicinesSerializer(page, many=True).data)
            return response.Ok(PatientAllopathicMedicinesSerializer(queryset, many=True).data)
        else:
            print('run post method')
            ser=PatientAllopathicMedicinesSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return response.Ok(ser.data)
            # return response.Ok(create_update_multiple_record(list(request.data), PatientAllopathicMedicinesSerializer,
            #                                                  PatientAllopathicMedicines))

    @action(methods=['POST'], detail=False)
    def generate_otp(self, request):
        data = request.data.copy()
        practice = data.get("practice", None)
        patient = data.get("patient", None)
        cancel_type = data["type"]
        practice_obj = None
        patient_obj = None
        mobile_no = None
        try:
            if practice:
                practice_obj = Practice.objects.get(id=practice)
            elif patient:
                patient_obj = Patients.objects.get(id=patient)
        except:
            response.BadRequest({"detail": "Please use correct Practice details"})
        otp = self.get_random_number(6)
        if practice:
            mobile_no = practice_obj.contact if practice_obj and practice_obj.contact else None
        elif patient:
            mobile_no = patient_obj.user.mobile if patient_obj and patient_obj.user else None
        user = request.user
        RequestOTP.objects.filter(user=user).update(is_active=False)
        if mobile_no:
            RequestOTP.objects.create(patient=patient_obj, practice=practice_obj, otp=otp, phone_no=mobile_no,
                                      user=user, cancel_type=cancel_type)
            send_sms_without_save(mobile_no, "OTP for " + str(cancel_type) + " is: " + str(otp))
            return response.Ok({"detail": "OTP sent successfully"})
        else:
            return response.BadRequest({"detail": "Please set mobile number in Practice details"})

    @action(methods=['GET'], detail=False)
    def resend_otp(self, request):
        user = request.user
        data = RequestOTP.objects.filter(is_active=True, user=user).first()
        send_sms_without_save(data.phone_no, "OTP for " + str(data.cancel_type) + " is: " + str(data.otp))
        return response.Ok({"detail": "OTP resent successfully"})

    @action(methods=['GET'], detail=True)
    def my_agents(self, request, *args, **kwargs):
        pagination = request.query_params.get("pagination", None)
        pagination = False if pagination == "false" else True
        patient = self.get_object()
        user = patient.user
        data = Patients.objects.filter(is_agent=True, is_active=True, user__referer=user)
        page = self.paginate_queryset(data)
        if pagination and page is not None:
            return self.get_paginated_response(PatientsSerializer(page, many=True).data)
        return response.Ok(PatientsSerializer(data, many=True).data)

    @action(methods=['GET'], detail=True)
    def agents_chain(self, request, *args, **kwargs):
        patient = self.get_object()
        users = [patient]
        max_chain = 5
        result = {}
        for i in range(max_chain):
            next_level = []
            current_level = []
            for user in users:
                current_level.append(PatientsReferalSerializer(user).data)
                next_level += list(Patients.objects.filter(is_agent=True, is_active=True, user__referer=user.user))
            result[i] = current_level
            users = next_level
        return response.Ok(result)

    @action(methods=['GET'], detail=True)
    def team_analysis(self, request, *args, **kwargs):
        patient = self.get_object()
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        sort = request.query_params.get('sort', None)
        users = [patient]
        patients = []
        max_chain = 5
        current_level = []
        for i in range(max_chain):
            next_level = []
            for user in users:
                patients.append(user)
                current_level.append(PatientsReferalSerializer(user).data)
                next_level += list(Patients.objects.filter(is_agent=True, is_active=True, user__referer=user.user))
            users = next_level
        invoices = get_advisor_sale(patients, start, end)
        for level in current_level:
            if level["user"]["id"] in invoices:
                level["sale"] = invoices[level["user"]["id"]]
            else:
                level["sale"] = 0.0
        if sort == "asc":
            current_level.sort(key=lambda k: k['sale'])
        else:
            current_level.sort(key=lambda k: k['sale'], reverse=True)
        return response.Ok(current_level)

    @action(methods=['POST'], detail=False)
    def verify_otp(self, request):
        data = request.data.copy()
        practice = data.get("practice", None)
        patient = data.get("patient", None)
        practice_obj = None
        patient_obj = None
        otp_data = None
        try:
            if practice:
                practice_obj = Practice.objects.get(id=practice)
            elif patient:
                patient_obj = Patients.objects.get(id=patient)
        except:
            response.BadRequest({"detail": "Please use correct Practice details"})
        user = request.user
        if practice:
            mobile_no = practice_obj.contact if practice_obj and practice_obj.contact else None
            print('modddd',mobile_no)
            otp_data = RequestOTP.objects.filter(user=user, practice=practice, phone_no=mobile_no,
                                                 is_active=True).first()
        elif patient:
            mobile_no = patient_obj.user.mobile if patient_obj and patient_obj.user else None
            otp_data = RequestOTP.objects.filter(user=user, patient=patient, phone_no=mobile_no, is_active=True).first()
        if otp_data and otp_data.otp and str(otp_data.otp) == str(data["otp"]):
            otp_data.is_active = False
            otp_data.save()
            return response.Ok({"detail": "OTP verified successfully"})
        else:
            return response.BadRequest({"detail": "Invalid OTP"})

    def get_random_number(self, N):
        from random import randint
        range_start = 10 ** (N - 1)
        range_end = (10 ** N) - 1
        return randint(range_start, range_end)

    @action(methods=['GET'], detail=False)
    def patient_list(self, request):
        queryset = Patients.objects.all()
        queryset = queryset.filter(is_active=True)
        gender = request.query_params.get("gender", None)
        age = request.query_params.get("age", None)
        type = request.query_params.get("type", None)
        group = request.query_params.get("group", None)
        agent = request.query_params.get("agent", None)
        role = request.query_params.get("role", None)
        name_starts = request.query_params.get("name_starts", None)
        name_equals = request.query_params.get("name_equals", None)
        query = request.query_params.get("query", None)
        perm_practice = request.query_params.get("perm_practice", None)
        pagination = request.query_params.get("pagination", 1)
        if gender:
            queryset = queryset.filter(gender=gender)
        if age:
            diff = date.today() - timedelta(days=365 * int(age))
            if type == 'lt':
                queryset = queryset.filter(dob__gte=diff)
            elif type == 'gt':
                queryset = queryset.filter(dob__lte=diff)
        if group:
            queryset = queryset.filter(patient_group=group)
        if name_starts:
            queryset = queryset.filter(user__first_name__istartswith=name_starts)
        if name_equals:
            queryset = queryset.filter(user__first_name=name_equals)
        if agent:
            is_agent = True if agent == 'true' else False
            queryset = queryset.filter(is_agent=is_agent)
        if role:
            queryset = queryset.filter(role=role)
        if perm_practice:
            queryset = queryset.filter(practices__practice=perm_practice)
        if query:
            find = [
                {"user__first_name__icontains": query},
                {"user__mobile__icontains": query},
                {"custom_id__icontains": query},
                {"aadhar_id__icontains": query},
                {"secondary_mobile_no__icontains": query},
                {"landline_no__icontains": query}
            ]
            queryset = self.add_filter(queryset, find)
        queryset = queryset.order_by('user__first_name')
        if int(pagination):
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(PatientsSerializer(page, many=True).data)
            return response.Ok(PatientsSerializer(queryset, many=True).data)
        else:
            return response.Ok(PatientsSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=True)
    def pending_amount(self, request, *args, **kwargs):
        practices = Practice.objects.filter(is_active=True)
        patient = self.get_object()
        grand_total = 0.0
        data = []
        for practice in practices:
            invoices = PatientInvoices.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                      practice=practice)
            payments = PatientPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                     practice=practice)
            returns = ReturnPayment.objects.filter(is_cancelled=False, is_active=True, patient=patient,
                                                   practice=practice)
            practice_total = 0.0
            for invoice in invoices:
                if invoice.total:
                    practice_total += invoice.total
            for payment in payments:
                if not payment.return_pay:
                    pay_total = payment.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0
                    advance = payment.advance_value if payment.advance_value else 0
                    practice_total -= (pay_total + advance)
            for return_pay in returns:
                cash = return_pay.cash_return if return_pay.cash_return else 0
                practice_total += cash
                if not return_pay.with_tax:
                    practice_total += return_pay.taxes if return_pay.with_tax else 0
            data.append({"name": practice.name, "total": round(practice_total, 2)})
            grand_total += practice_total
        return response.Ok({"grand_total": round(grand_total, 2), "practice_data": data})

    @action(methods=['GET', 'POST'], detail=False)
    def city(self, request):
        if request.method == "GET":
            state = request.query_params.get("state", None)
            if state:
                queryset = City.objects.filter(is_active=True, state=state)
                return response.Ok(CitySerializer(queryset.order_by("name"), many=True).data)
            else:
                return response.BadRequest({"detail": "Send state in query params"})
        else:
            return response.Ok(create_update_record(request, CitySerializer, City))

    @action(methods=['GET', 'POST'], detail=False)
    def state(self, request):
        if request.method == "GET":
            country = request.query_params.get("country", None)
            if country:
                queryset = State.objects.filter(is_active=True, country=country)
                return response.Ok(StateSerializer(queryset.order_by("name"), many=True).data)
            else:
                return response.BadRequest({"detail": "Send country in query params"})
        else:
            return response.Ok(create_update_record(request, StateSerializer, State))

    @action(methods=['GET', 'POST'], detail=False)
    def country(self, request):
        if request.method == "GET":
            queryset = Country.objects.filter(is_active=True)
            return response.Ok(CountrySerializer(queryset.order_by("name"), many=True).data)
        else:
            return response.Ok(create_update_record(request, CountrySerializer, Country))

    @action(methods=['GET'], detail=False)
    def source(self, request):
        queryset = Source.objects.filter(is_active=True)
        return response.Ok(SourceSerializer(queryset.order_by("name"), many=True).data)

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def bank_details(self, request, *args, **kwargs):
        if request.method == "GET":
            patient = request.query_params.get("patient", None)
            pagination = request.query_params.get("pagination", None)
            pagination = False if pagination == "false" else True
            queryset = AdvisorBank.objects.filter(is_active=True)
            if patient:
                queryset = queryset.filter(patient=patient)
            page = self.paginate_queryset(queryset)
            if pagination and page is not None:
                return self.get_paginated_response(AdvisorBankDataSerializer(page, many=True).data)
            return response.Ok(AdvisorBankDataSerializer(queryset.order_by("-id"), many=True).data)
        else:
            return response.Ok(create_update_record(request, AdvisorBankSerializer, AdvisorBank))

    @action(methods=['GET', 'POST'], detail=False)
    def cold_calling(self, request):
        if request.method == 'GET':
            call_id = request.query_params.get('id', None)
            city = request.query_params.get('city', None)
            state = request.query_params.get('state', None)
            country = request.query_params.get('country', None)
            mobile = request.query_params.get('mobile', None)
            medical_history = request.query_params.get('medical_history', None)
            created_advisor = request.query_params.get('created_advisor', None)
            created_staff = request.query_params.get('created_staff', None)
            data = ColdCalling.objects.filter(is_active=True)
            if call_id:
                data = data.filter(id=call_id)
            if city:
                data = data.filter(city=city)
            if state:
                data = data.filter(state=state)
            if country:
                data = data.filter(country=country)
            if mobile:
                data = data.filter(mobile__icontains=mobile)
            if medical_history:
                medical_list = medical_history.split(",")
                data = data.filter(medical_history__in=medical_list)
            if created_advisor:
                advisor_list = created_advisor.split(",")
                data = data.filter(created_advisor__in=advisor_list)
            if created_staff:
                staff_list = created_staff.split(",")
                data = data.filter(created_staff__in=staff_list)
            data = data.order_by('-id')
            page = self.paginate_queryset(data)
            if page is not None:
                return self.get_paginated_response(ColdCallingDataSerializer(page, many=True).data)
            return response.Ok(ColdCallingDataSerializer(data, many=True).data)
        else:
            return response.Ok(create_update_record(request, ColdCallingSerializer, ColdCalling))

    @action(methods=['POST'], detail=False)
    def merge_patients(self, request, *args, **kwargs):
        from ..appointment.models import Appointment
        patient_from_id = request.data.get('patient_from', None)
        patient_to_id = request.data.get('patient_to', None)
        if patient_from_id == patient_to_id:
            return response.BadRequest({"detail": "Both Patients cannot be same"})
        else:
            patient_from = Patients.objects.filter(id=patient_from_id, is_active=True).values()
            patient_to = Patients.objects.filter(id=patient_to_id, is_active=True).values()
            if len(patient_from) and len(patient_to):
                patient_to = patient_to[0]
                patient_from = patient_from[0]
                for key in patient_to.keys():
                    if not patient_to[key]:
                        patient_to[key] = patient_from[key]
                Patients.objects.filter(id=patient_to_id).update(**patient_to)
                Appointment.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientVitalSigns.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientClinicNotes.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientProcedure.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientFile.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientPrescriptions.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientInvoices.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientPayment.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                Reservations.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientWalletLedger.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientWallet.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientMembership.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                PatientNotes.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                ReturnPayment.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                MedicalCertificate.objects.filter(patient=patient_from_id).update(patient=patient_to_id)
                Patients.objects.filter(id=patient_from_id).update(is_active=False)
                User.objects.filter(id=patient_from["user_id"]).update(is_active=False)
                instance = Patients.objects.get(id=patient_to_id)
                instance.save()
                return response.Ok({"detail": "Patients Merged Successfully"})
            elif len(patient_from) and not len(patient_to):
                return response.BadRequest({"detail": "Patient 2 does not exists"})
            elif not len(patient_from) and len(patient_to):
                return response.BadRequest({"detail": "Patient 1 does not exists"})
            elif not len(patient_from) and not len(patient_to):
                return response.BadRequest({"detail": "Both Patients do not exists"})

    @action(methods=['GET'], detail=True)
    def patient_appointments(self, request, *args, **kwargs):
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        from ..appointment.models import Appointment
        from ..appointment.serializers import AppointmentSerializer
        # THis api will give patient all data in one place
        instance = self.get_object()
        appointments = Appointment.objects.filter(patient=instance)
        if start:
            start = timezone.get_day_start(timezone.from_str(start))
            appointments = appointments.filter(created_at__gte=start)
        if end:
            end = timezone.get_day_end(timezone.from_str(end))
            appointments = appointments.filter(created_at__lte=end)
        appointments.order_by('-schedule_at')
        page = self.paginate_queryset(appointments)
        if page is not None:
            return self.get_paginated_response(AppointmentSerializer(page, many=True).data)
        return response.Ok(AppointmentSerializer(appointments, many=True).data)

    @action(methods=['GET'], detail=True)
    def combine_patient_report(self, request, *args, **kwargs):
        instance = self.get_object()
        response_list = generate_timeline(instance, request.query_params)
        return response.Ok(response_list)

    @action(methods=['POST'], detail=True)
    def timeline_pdf(self, request, *args, **kwargs):
        instance = self.get_object()
        req_data = request.data.copy()
        data = req_data.get("timeline", [])
        mail_to = req_data.get("mail_to", None)
        practice = req_data.get("practice", [])
        patient_name = instance.user.first_name if instance.user and instance.user.first_name else "User"
        required_data = {}
        flat_list = []
        for part in data:
            part_type = part.get("type", None)
            ids = part.get("id", [])
            if part_type and len(ids) > 0:
                required_data[part_type.lower().replace(" ", "_")] = True
            for id in ids:
                flat_list.append({"id": int(id), "type": part_type})
        response_list = generate_timeline(instance, required_data)
        final_response = []
        for flat_data in flat_list:
            for resp in response_list:
                if str(resp["id"]) == str(flat_data["id"]) and resp["type"] == flat_data["type"]:
                    final_response.append(resp)
                    break
        pdf_obj = generate_pdf("EMR", "CASE SHEET", final_response, None, None,
                               practice, instance.pk, None, "case_sheet.html", "CaseSheetID")
        result = GeneratedPdfSerializer(pdf_obj).data
        if mail_to:
            result = mail_file(patient_name, mail_to, pdf_obj, practice, "Case Sheet")
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET'], detail=False)
    def new_patients(self, request, *args, **kwargs):
        mail_to = request.query_params.get("mail_to", None)
        from_date = request.query_params.get("from_date", None)
        to_date = request.query_params.get("to_date", None)
        follow_start = request.query_params.get("follow_start", None)
        follow_end = request.query_params.get("follow_end", None)
        groups = request.query_params.get("groups", None)
        blood_group = request.query_params.get("blood_group", None)
        report_type = request.query_params.get("type", None)
        source = request.query_params.get("source", None)
        queryset = Patients.objects.filter(is_active=True)
        practice_name = CONST_GLOBAL_PRACTICE
        if from_date and to_date:
            start = from_date
            end = to_date
            from_date = timezone.get_day_start(pd.to_datetime(from_date))
            to_date = timezone.get_day_end(pd.to_datetime(to_date))
            queryset = queryset.filter(created_at__range=[from_date, to_date])
        if groups:
            group_list = groups.split(",")
            queryset = queryset.filter(patient_group__in=group_list)
        if blood_group:
            queryset = queryset.filter(blood_group=blood_group)
        if source:
            queryset = queryset.filter(source=source)
        if report_type == "MONTHLY":
            total = queryset.count()
            queryset = queryset.annotate(year=Year('created_at'), month=Month('created_at')).values('year',
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
                subject = "Monthly New Patient Report from " + from_date.strftime(
                    "%d/%m/%Y") + " to " + to_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Monthly New Patient Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_New_Patient_" + start + "_" + end, mail_to, subject,
                                          body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DAILY":
            total = queryset.count()
            queryset = queryset.annotate(year=Year('created_at'), month=Month('created_at'),
                                         day=Day('created_at')).values('year', 'month', 'day').annotate(
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
                        {"Date": pd.to_datetime(item["date"]).strftime("%d/%m/%Y"), "Count": item["count"]})
                subject = "Daily New Patient Report from " + from_date.strftime(
                    "%d/%m/%Y") + " to " + to_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Daily New Patient Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_New_Patient_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "SOURCE":
            queryset = queryset.values('source', 'source__name').annotate(count=Count('*')).order_by('-count')
            result = {"data": queryset}
            if mail_to:
                ready_data = []
                for item in queryset:
                    ready_data.append(
                        {"source": item["source__name"] if item["source__name"] else "No Source",
                         "Count": item["count"]})
                subject = "Source wise new patient Report from " + from_date.strftime(
                    "%d/%m/%Y") + " to " + to_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Source wise New Patient Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Source_New_Patient" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "DETAILED":
            if mail_to:
                ready_data = []
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Patient Name": item.user.first_name if item.user and item.user.first_name else "--",
                        "Patient Number": item.custom_id if item.custom_id else item.id,
                        "Mobile No.": item.user.mobile if item.user and item.user.mobile else "--",
                        "Email Id": item.user.email if item.user and item.user.email else "--",
                        "Gender": item.gender if item.gender else "--"
                    })
                subject = "New Patient Report from " + from_date.strftime(
                    "%d/%m/%Y") + " to " + to_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the New Patient Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "New_Patient_" + start + "_" + end, mail_to, subject, body)
                result = {"detail": msg, "error": error}
            else:
                result = PatientsBasicDataSerializer(queryset, many=True).data
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "FOLLOW_UP":
            if follow_start and follow_end:
                follow_start_date = pd.to_datetime(follow_start)
                follow_end_date = pd.to_datetime(follow_end)
                queryset = queryset.filter(follow_up_date__range=[follow_start_date, follow_end_date])
            if mail_to:
                ready_data = []
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Patient Name": item.user.first_name if item.user and item.user.first_name else "--",
                        "Patient Number": item.custom_id if item.custom_id else item.id,
                        "Mobile No.": item.user.mobile if item.user and item.user.mobile else "--",
                        "Email Id": item.user.email if item.user and item.user.email else "--",
                        "Gender": item.gender if item.gender else "--",
                        "Follow Up On": item.follow_up_date.strftime("%d/%m/%Y") if item.follow_up_date else "--"
                    })
                subject = "New Patient Follow up Report from " + follow_start_date.strftime(
                    "%d/%m/%Y") + " to " + follow_end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the New Patient Follow up Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "New_Patient_Follow_" + follow_start + "_" + follow_end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}
            else:
                result = PatientsFollowUpSerializer(queryset, many=True).data
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "MEDICINE":
            if follow_start and follow_end:
                follow_start_date = pd.to_datetime(follow_start)
                follow_end_date = pd.to_datetime(follow_end)
                queryset = queryset.filter(medicine_till__range=[follow_start_date, follow_end_date])
            if mail_to:
                ready_data = []
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Patient Name": item.user.first_name if item.user and item.user.first_name else "--",
                        "Patient Number": item.custom_id if item.custom_id else item.id,
                        "Mobile No.": item.user.mobile if item.user and item.user.mobile else "--",
                        "Email Id": item.user.email if item.user and item.user.email else "--",
                        "Gender": item.gender if item.gender else "--",
                        "Medicine From": item.medicine_from.strftime("%d/%m/%Y") if item.medicine_from else "--",
                        "Medicine Till": item.medicine_till.strftime("%d/%m/%Y") if item.medicine_till else "--"
                    })
                subject = "Patient Medicine Report from " + follow_start_date.strftime(
                    "%d/%m/%Y") + " to " + follow_end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the Patient Medicine Report in the attachment." \
                       + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Patient_Medicine_" + follow_start + "_" + follow_end,
                                          mail_to, subject, body)
                result = {"detail": msg, "error": error}
            else:
                result = PatientsFollowUpSerializer(queryset, many=True).data
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        else:
            return response.BadRequest({"detail": "Invalid type sent"})

    @action(methods=['GET'], detail=False)
    def membership_report(self, request, *args, **kwargs):
        from_date = request.query_params.get("from_date", None)
        to_date = request.query_params.get("to_date", None)
        type = request.query_params.get("type", None)
        queryset = PatientMembership.objects.filter(is_active=True)
        if type == "NEW" and from_date and to_date:
            queryset = queryset.filter(medical_from__lte=to_date, medical_from__gte=from_date)
        elif type == "EXPIRED" and from_date and to_date:
            queryset = queryset.filter(medical_to__lte=to_date, medical_to__gte=from_date)
        else:
            return response.BadRequest({"detail": "Invalid parameters sent"})
        return response.Ok(PatientMembershipReportSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=False)
    def registration_report(self, request, *args, **kwargs):
        from_date = request.query_params.get("from_date", None)
        to_date = request.query_params.get("to_date", None)
        type = request.query_params.get("type", None)
        print(type)
        queryset = PatientRegistration.objects.filter(is_active=True)
        if type == "NEW" and from_date and to_date:
            queryset = queryset.filter(registration_from__lte=to_date, registration_from__gte=from_date)
        elif type == "EXPIRED" and from_date and to_date:
            queryset = queryset.filter(registration_to__lte=to_date, registration_to__gte=from_date)
        else:
            return response.BadRequest({"detail": "Invalid parameters sent"})
        return response.Ok(PatientRegistrationReportSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def calling_report(self, request, *args, **kwargs):
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        call_type = request.query_params.get("type", None)
        practice = request.query_params.get("practice", None)
        patient = request.query_params.get("patient", None)
        call_response = request.query_params.get("response", None)
        practice_staff = request.query_params.get("practice_staff", None)
        mail_to = request.query_params.get("mail_to", None)
        queryset = PatientCallNotes.objects.filter(is_active=True)
        practice_name = CONST_GLOBAL_PRACTICE
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if call_type:
            queryset = queryset.filter(type=call_type)
        if practice_staff:
            queryset = queryset.filter(practice_staff=practice_staff)
        if call_response:
            queryset = queryset.fcilter(response=call_response)
        if practice:
            queryset = queryset.filter(practice=practice)
            practice_obj = Practice.objects.filter(id=practice).first()
            practice_name = practice_obj.name if practice_obj else CONST_GLOBAL_PRACTICE
        if patient:
            queryset = queryset.filter(patient=patient)
        if mail_to:
            ready_data = []
            for index, item in enumerate(queryset):
                ready_data.append({
                    "S. No.": index + 1,
                    "Staff Name": item.practice_staff.user.first_name \
                        if item.practice_staff and item.practice_staff.user.first_name else "--",
                    "Staff ID": item.practice_staff.emp_id if item.practice_staff and item.practice_staff.emp_id else "--",
                    "Patient Name": item.patient.user.first_name if item.patient and item.patient.user.first_name else "--",
                    "Patient ID": item.patient.custom_id if item.patient.custom_id else "--",
                    "Patient Mobile": item.patient.user.mobile if item.patient and item.patient.user.mobile else "--",
                    "Type": item.type if item.type else "--",
                    "Response": item.response if item.response else "--",
                    "Remarks": item.remarks if item.remarks else "--",
                })
            subject = "Call Details Report from " + start.strftime("%d/%m/%Y") + " to " + end.strftime("%d/%m/%Y")
            body = "As Requested on ERP System, Please find the Call Details Report in the attachment." \
                   + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Call_Details_" + start + "_" + end, mail_to, subject, body)
            result = {"detail": msg, "error": error}
            return response.Ok(result)
        else:
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(PatientCallNotesDetailSerializer(page, many=True).data)
            return response.Ok(PatientCallNotesDetailSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=False)
    def first_appointment(self, request, *args, **kwargs):
        from_date = request.query_params.get("from_date", None)
        to_date = request.query_params.get("to_date", None)
        appointments = Appointment.objects.filter(is_active=True).order_by('patient', 'schedule_at').distinct('patient')
        patients = []
        if from_date and to_date:
            for appointment in appointments:
                if appointment.patient and appointment.schedule_at:
                    schedule_time_no_tz = (appointment.schedule_at + timedelta(minutes=330)).replace(tzinfo=None)
                    if schedule_time_no_tz <= pd.to_datetime(to_date) and schedule_time_no_tz >= pd.to_datetime(
                            from_date):
                        patient_name = appointment.patient.user.first_name
                        patient_id = appointment.patient.custom_id if appointment.patient.custom_id else appointment.patient.pk
                        appointment_time = appointment.schedule_at
                        patients.append({"patient_name": patient_name, "patient_id": patient_id,
                                         "appointment_time": appointment_time})
            return response.Ok(patients)
        else:
            return response.BadRequest({"detail": "Invalid from_date / to_date sent"})

    @action(methods=['GET'], detail=False)
    def search(self, request, *args, **kwargs):
        patient_name = request.query_params.get("name", None)
        perm_practice = request.query_params.get("perm_practice", None)
        if patient_name:
            find = [
                {"user__first_name__icontains": patient_name},
                {"user__mobile__icontains": patient_name},
                {"custom_id__icontains": patient_name},
                {"aadhar_id__icontains": patient_name},
                {"secondary_mobile_no__icontains": patient_name},
                {"landline_no__icontains": patient_name}
            ]
            patients = self.add_filter(Patients.objects.filter(is_active=True), find)
            if perm_practice:
                patients = patients.filter(practices__practice=perm_practice)
            patients = patients.order_by('user__first_name')
            page = self.paginate_queryset(patients)
            if page is not None:
                return self.get_paginated_response(PatientsSerializer(page, many=True).data)
            return response.Ok(PatientsSerializer(patients, many=True).data)
        return response.BadRequest({"detail": "Send Name in Query Params"})

    def add_filter(self, queryset, dictionary):
        data = Patients.objects.none()
        for filter in dictionary:
            data = data | queryset.filter(**filter)
        return data.distinct()

    @action(methods=['GET'], detail=False)
    def advance_search(self, request, *args, **kwargs):
        patient_name = request.query_params.get("name", None)
        phone = request.query_params.get("phone", None)
        age = request.query_params.get("age", None)
        age_gte = request.query_params.get("age_gte", None)
        age_lte = request.query_params.get("age_lte", None)
        has_age = request.query_params.get("has_age", None)
        dob = request.query_params.get("dob", None)
        dob_gte = request.query_params.get("dob_gte", None)
        dob_lte = request.query_params.get("dob_lte", None)
        dob_month = request.query_params.get("dob_month", None)
        has_dob = request.query_params.get("has_dob", None)
        patient_id = request.query_params.get("patient_id", None)
        aadhar = request.query_params.get("aadhar", None)
        has_aadhar = request.query_params.get("has_aadhar", None)
        email = request.query_params.get("email", None)
        has_email = request.query_params.get("has_email", None)
        gender = request.query_params.get("gender", None)
        has_gender = request.query_params.get("has_gender", None)
        pincode = request.query_params.get("pincode", None)
        has_pincode = request.query_params.get("has_pincode", None)
        street = request.query_params.get("street", None)
        has_street = request.query_params.get("has_street", None)
        blood_group = request.query_params.get("blood_group", None)
        source = request.query_params.get("source", None)
        agent_referal = request.query_params.get("agent_referal", None)
        country = request.query_params.get("country", None)
        state = request.query_params.get("state", None)
        city = request.query_params.get("city", None)
        perm_practice = request.query_params.get("perm_practice", None)
        patients = Patients.objects.filter(is_active=True)
        if patient_name:
            patients = patients.filter(user__first_name__icontains=patient_name)
        if phone:
            patients = patients.filter(user__mobile__icontains=phone)
        if age:
            from_date = date.today() - timedelta(days=365 * int(age - 1))
            to_date = date.today() - timedelta(days=365 * int(age + 1))
            patients = patients.filter(dob__gt=from_date, dob__lt=to_date)
        if age_gte:
            from_date = date.today() - timedelta(days=365 * int(age_gte))
            patients = patients.filter(dob__lte=from_date)
        if age_lte:
            from_date = date.today() - timedelta(days=365 * int(age_lte))
            patients = patients.filter(dob__gte=from_date)
        if has_age and has_age == 'Y':
            patients = patients.filter(is_age=True)
        elif has_age and has_age == 'N':
            patients = patients.filter(is_age=False)
        if dob:
            patients = patients.filter(is_age=False, dob=dob)
        if dob_gte:
            patients = patients.filter(dob__gte=dob_gte)
        if dob_lte:
            patients = patients.filter(dob__lte=dob_lte)
        if dob_month:
            patients = patients.filter(is_age=False, dob__month=dob_month)
        if has_dob and has_dob == 'Y':
            patients = patients.filter(is_age=False)
        elif has_dob and has_dob == 'N':
            patients = patients.filter(is_age=True)
        if patient_id:
            patients = patients.filter(custom_id__icontains=patient_id)
        if aadhar:
            patients = patients.filter(aadhar_id__icontains=aadhar)
        if has_aadhar and has_aadhar == 'Y':
            patients = patients.exclude(aadhar_id=None)
        elif has_aadhar and has_aadhar == 'N':
            patients = patients.filter(aadhar_id=None)
        if email:
            patients = patients.filter(user__email__icontains=email)
        if has_email and has_email == 'Y':
            patients = patients.exclude(user__email=None)
        elif has_email and has_email == 'N':
            patients = patients.filter(user__email=None)
        if gender:
            patients = patients.filter(gender=gender)
        if has_gender and has_gender == 'Y':
            patients = patients.exclude(gender=None)
        elif has_gender and has_gender == 'N':
            patients = patients.filter(gender=None)
        if pincode:
            patients = patients.filter(pincode__icontains=pincode)
        if has_pincode and has_pincode == 'Y':
            patients = patients.exclude(pincode=None)
        elif has_pincode and has_pincode == 'N':
            patients = patients.filter(pincode=None)
        if street:
            patients = patients.filter(locality__icontains=street) | patients.filter(address__icontains=street)
        if has_street and has_street == 'Y':
            patients = patients.exclude(locality=None)
        elif has_street and has_street == 'N':
            patients = patients.filter(locality=None)
        if blood_group:
            patients = patients.filter(blood_group__icontains=blood_group)
        if source:
            patients = patients.filter(source=source)
        if country:
            patients = patients.filter(country=country)
        if state:
            patients = patients.filter(state=state)
        if city:
            patients = patients.filter(city=city)
        if agent_referal and agent_referal == 'Y':
            patients = patients.exclude(user__referer=None)
        elif agent_referal and agent_referal == 'N':
            patients = patients.filter(user__referer=None)
        if perm_practice:
            patients = patients.filter(practices__practice=perm_practice)
        page = self.paginate_queryset(patients.order_by('user__first_name'))
        if page is not None:
            return self.get_paginated_response(PatientsBasicDataSerializer(page, many=True).data)
        return response.Ok(PatientsBasicDataSerializer(patients.order_by('user__first_name'), many=True).data)

    @action(methods=['GET', 'POST'], detail=False)
    def membership(self, request, *args, **kwargs):
        patient_id = request.query_params.get("patient", None)
        if request.method == 'GET':
            data = PatientMembership.objects.filter(is_active=True, medical_to__gte=datetime.today().date())
            if patient_id:
                data = data.filter(patient=patient_id)
            return response.Ok(PatientMembershipDataSerializer(data, many=True).data)
        else:
            data = request.data.copy()
            patient_id = data.get("patient", None)
            practice_id = data.get("practice", None)
            staff_id = PracticeStaff.objects.filter(user=request.user.id).first()
            data["staff"] = staff_id.id
            membership_id = data.get("medical_membership", None)
            if membership_id:
                try:
                    membership_data = Membership.objects.get(id=membership_id)
                except:
                    return response.BadRequest({'detail': 'Send a Valid Membership Id with data.'})
                months = membership_data.validity if membership_data.validity else 0
                fee = membership_data.fee if membership_data.fee else 0
                practice_obj = Practice.objects.get(id=practice_id)
                prefix = practice_obj.invoice_prefix if practice_obj and practice_obj.invoice_prefix else ""
                if fee > 0:
                    invoice_data = {
                        "practice": practice_obj,
                        "patient": Patients.objects.get(id=patient_id),
                        "staff": staff_id,
                        "cost": fee,
                        "total": fee,
                        "date": datetime.today().date(),
                        "type": CONST_MEMBERSHIP,
                        "invoice_id": prefix + str(PatientInvoices.objects.filter(practice=practice_obj).count() + 1)
                    }
                    invoice = PatientInvoices.objects.create(**invoice_data)
                    data["membership_invoice"] = invoice.id
                data["medical_to"] = (pd.to_datetime(data["medical_from"]) + relativedelta(months=months)).date()
                letters = string.ascii_uppercase + string.digits
                random_str = ''.join(random.choice(letters) for i in range(8))
                while PatientMembership.objects.filter(membership_code=random_str).exists():
                    random_str = ''.join(random.choice(letters) for i in range(8))
                data["membership_code"] = random_str
                serializer = PatientMembershipSerializer(data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer = serializer.save()
                return response.Ok(PatientMembershipSerializer(serializer).data)
            else:
                return response.BadRequest({'detail': 'Send Membership Id with data.'})

    @action(methods=['POST'], detail=False)
    def cancel_membership(self, request, *args, **kwargs):
        data = request.data.copy()
        id = data.get("id", None)
        if id:
            try:
                membership_data = PatientMembership.objects.get(id=id)
            except:
                return response.BadRequest({'detail': 'Send a Valid Patient Membership Id with data.'})
            invoice = membership_data.membership_invoice
            payment = membership_data.membership_payments
            inv_data = PatientInvoicesDataSerializer(invoice).data
            if payment:
                pay_obj = PatientPayment.objects.get(id=payment.pk)
                pay_obj.is_cancelled = True
                pay_obj.save()
            if "payments_data" in inv_data and inv_data["payments_data"] and int(inv_data["payments_data"]) > 0:
                return response.BadRequest({"detail": "Payment has been received. Cannot cancel this Membership."})
            if invoice:
                inv_obj = PatientInvoices.objects.get(id=invoice.pk)
                inv_obj.is_cancelled = True
                inv_obj.save()
            membership_data.is_active = False
            membership_data.save()
            return response.Ok({"detail": "Patient Membership Cancelled Successfully"})

    @action(methods=['GET', 'POST'], detail=False)
    def registration(self, request, *args, **kwargs):
        patient_id = request.query_params.get("patient", None)
        if request.method == 'GET':
            data = PatientRegistration.objects.filter(is_active=True, registration_to__gte=datetime.today().date())
            last_data = PatientRegistration.objects.filter(is_active=True)
            if patient_id:
                data = data.filter(patient=patient_id)
                last_data = last_data.filter(patient=patient_id)
            if data.count() > 0:
                return response.Ok(PatientRegistrationDataSerializer(data, many=True).data)
            elif last_data:
                return response.Ok(
                    [PatientRegistrationDataSerializer(last_data.order_by('-registration_to').first()).data])
            else:
                return response.Ok([])
        else:
            data = request.data.copy()
            patient_id = data.get("patient", None)
            practice_id = data.get("practice", None)
            staff_id = PracticeStaff.objects.filter(user=request.user.id).first()
            data["staff"] = staff_id.id
            registration_id = data.get("registration", None)
            if registration_id:
                try:
                    registration_data = Registration.objects.get(id=registration_id)
                except:
                    return response.BadRequest({'detail': 'Send a Valid Registration Id with data.'})
                days = registration_data.validity - 1 if registration_data.validity else 0
                fee = registration_data.fee if registration_data.fee else 0
                practice_obj = Practice.objects.get(id=practice_id)
                prefix = practice_obj.invoice_prefix if practice_obj and practice_obj.invoice_prefix else ""
                if fee > 0:
                    invoice_data = {
                        "practice": practice_obj,
                        "patient": Patients.objects.get(id=patient_id),
                        "staff": staff_id,
                        "cost": fee,
                        "total": fee,
                        "date": datetime.today().date(),
                        "type": CONST_REGISTRATION,
                        "invoice_id": prefix + str(PatientInvoices.objects.filter(practice=practice_obj).count() + 1)
                    }
                    invoice = PatientInvoices.objects.create(**invoice_data)
                    data["registration_invoice"] = invoice.id
                data["registration_to"] = (pd.to_datetime(data["registration_from"]) + relativedelta(days=days)).date()
                serializer = PatientRegistrationSerializer(data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer = serializer.save()
                return response.Ok(PatientRegistrationSerializer(serializer).data)
            else:
                return response.BadRequest({'detail': 'Send Registration Id with data.'})

    @action(methods=['POST'], detail=False)
    def cancel_registration(self, request, *args, **kwargs):
        data = request.data.copy()
        id = data.get("id", None)
        if id:
            try:
                registration_data = PatientRegistration.objects.get(id=id)
            except:
                return response.BadRequest({'detail': 'Send a Valid Patient Registration Id with data.'})
            invoice = registration_data.registration_invoice
            payment = registration_data.registration_payments
            inv_data = PatientInvoicesDataSerializer(invoice).data
            if payment:
                pay_obj = PatientPayment.objects.get(id=payment.pk)
                pay_obj.is_cancelled = True
                pay_obj.save()
            if "payments_data" in inv_data and inv_data["payments_data"] and int(inv_data["payments_data"]) > 0:
                return response.BadRequest({"detail": "Payment has been received. Cannot cancel this Registration."})
            if invoice:
                inv_obj = PatientInvoices.objects.get(id=invoice.pk)
                inv_obj.is_cancelled = True
                inv_obj.save()
            registration_data.is_active = False
            registration_data.save()
            return response.Ok({"detail": "Patient Registration Cancelled Successfully"})

    @action(methods=['GET', 'POST'], detail=False)
    def group(self, request, *args, **kwargs):
        practice_id = request.query_params.get("id", None)
        instance = Practice.objects.get(id=practice_id) if practice_id else None
        if request.method == 'GET':
            queryset = PatientGroups.objects.filter(is_active=True)
            return response.Ok(PatientGroupsSerializer(queryset, many=True).data)
        else:
            update_response = update_pratice_patient_details(request, PatientGroupsSerializer, instance,
                                                             PatientGroups)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET'], detail=False)
    def active_patients(self, request, *args, **kwargs):
        groups = request.query_params.get("groups", None)
        mail_to = request.query_params.get("mail_to", None)
        blood_group = request.query_params.get("blood_group", None)
        end = datetime.today()
        start = datetime.today() - timedelta(days=90)
        practice_name = CONST_GLOBAL_PRACTICE
        invoices = PatientInvoices.objects.exclude(is_cancelled=True, is_active=False).filter(
            date__range=[start, end]).values_list('patient', flat=True)
        payments = PatientPayment.objects.exclude(is_cancelled=True, is_active=False).filter(
            date__range=[start, end]).values_list('patient', flat=True)
        appointments = Appointment.objects.exclude(status=CONST_CANCELLED, is_active=False).filter(
            schedule_at__range=[start, end]).values_list('patient', flat=True)
        all_patients = list(invoices) + list(payments) + list(appointments)
        patients = Patients.objects.filter(id__in=all_patients, is_dead=False)
        if groups:
            group_list = groups.split(",")
            patients = patients.filter(patient_group__in=group_list)
        if blood_group:
            patients = patients.filter(blood_group=blood_group)
        result = PatientsSerializer(patients, many=True).data
        ready_data = []
        if mail_to:
            for index, item in enumerate(result):
                ready_data.append({
                    "S. No.": index + 1,
                    "Patient Name": item["user"]["first_name"],
                    "Patient ID": item["custom_id"],
                    "Mobile Number": item["user"]["mobile"],
                    "Email": item["user"]["email"] if item["user"]["email"] else "--",
                    "Gender": item["gender"] if item["gender"] else "--"
                })
            subject = "Active Patients Report from " + start.strftime("%d/%m/%Y") + " to " + end.strftime("%d/%m/%Y")
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data,
                                      "Active_Patients_Report_" + start.strftime("%d-%m-%Y") + "_" + end.strftime(
                                          "%d-%m-%Y"), mail_to, subject, body)
            result = {"detail": msg, "error": error}
        if "error" in result and result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET', 'POST'], detail=False)
    def history(self, request, *args, **kwargs):
        pratice_id = request.query_params.get("id", None)
        instance = Practice.objects.get(id=pratice_id) if pratice_id else None
        if request.method == 'GET':
            deleted = request.query_params.get("deleted", None)
            if deleted:
                return response.Ok(
                    PatientMedicalHistorySerializer(
                        PatientMedicalHistory.objects.filter(is_active=False).order_by('-id'),
                        many=True).data)
            else:
                return response.Ok(PatientMedicalHistorySerializer(
                    PatientMedicalHistory.objects.filter(is_active=True).order_by('-id'),
                    many=True).data)
        else:
            update_response = update_pratice_patient_details(request, PatientMedicalHistorySerializer, instance,
                                                             PatientMedicalHistory)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=False)
    def vital_sign(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        get_serializer = PatientVitalSignsSerializer
        post_serializer = PatientVitalSignsSerializer
        model = PatientVitalSigns
        sort_on = "-date"
        return common_function(self, request, patient_id, practice_id, get_serializer, post_serializer, model, sort_on)

    @action(methods=['GET'], detail=False)
    def vital_sign_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    vital_signs_obj = PatientVitalSigns.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Vital Signs Records Exists"})
                practice = vital_signs_obj.practice.pk if vital_signs_obj.practice else None
                patient = vital_signs_obj.patient.pk if vital_signs_obj.patient else None
                patient_name = vital_signs_obj.patient.user.first_name if vital_signs_obj.patient and vital_signs_obj.patient.user else "User"
                doctor = vital_signs_obj.doctor.pk if vital_signs_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "REPORT MANUAL", PatientVitalSigns, PatientVitalSignsSerializer, id,
                                       practice, patient, doctor, "vital_signs.html", "VitalSignID")
                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "Report Manual")
                if "error" in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Vital Sign Id in Query Params'})

    @action(methods=['GET', 'POST'], detail=False)
    def clinic_notes(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        data = request.data.copy()
        follow_up_date = data.pop("follow_up_date", None)
        get_serializer = PatientClinicNotesDataSerializer
        post_serializer = PatientClinicNotesSerializer
        model = PatientClinicNotes
        sort_on = "-date"
        resp = common_function(self, request, patient_id, practice_id, get_serializer, post_serializer, model, sort_on)
        if request.method == 'POST' and resp.status_code == 200:
            instance = Patients.objects.get(id=patient_id)
            if follow_up_date:
                instance.follow_up_date = follow_up_date
                instance.save()
        return resp

    @action(methods=['GET', 'POST'], detail=False)
    def procedure(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        if request.method == 'GET':
            is_complete = True if request.query_params.get("complete", None) == 'true' else False
            practice = request.query_params.get("practice", None)
            data = PatientProcedure.objects.filter(is_active=True)
            if is_complete:
                data = data.filter(treatment_plans__is_completed=True)
            if patient_id:
                data = data.filter(patient=patient_id)
            if practice:
                data = data.filter(practice=practice)
            data = data.distinct().order_by('-date')
            page = self.paginate_queryset(data)
            if page is not None:
                return self.get_paginated_response(PatientProcedureDataSerializer(page, many=True).data)
            return response.Ok(PatientProcedureDataSerializer(data, many=True).data)
        else:
            if patient_id:
                instance = Patients.objects.get(id=patient_id)
                update_response = update_patient_procedure(request, PatientProcedureSerializer, instance,
                                                           PatientProcedure)
                return response.Ok(update_response) if update_response else response.BadRequest(
                    {'detail': 'Send id with data'})
            else:
                return response.BadRequest({'detail': 'Send patient with data'})

    @action(methods=['POST'], detail=False)
    def complete_procedure(self, request, *args, **kwargs):
        data = request.data.copy()
        treatments = data.get("treatment", None)
        for treatment in treatments:
            treatment_id = treatment.get("id", None)
            treatment_status = treatment.get("is_completed", False)
            if treatment_id:
                PatientTreatmentPlans.objects.filter(id=treatment_id).update(is_completed=treatment_status)
        if len(treatments):
            return response.Ok({"detail": "Treatment Plans updated successfully"})
        else:
            return response.BadRequest({"detail": "No Treatment Plans Selected"})

    @action(methods=['GET', 'POST'], detail=False)
    def files(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
            practice_id = request.query_params.get("practice", None)
            tag = request.query_params.get("tag", None)
            upload_by = request.query_params.get("upload_by", None)
            notag = request.query_params.get("notag", None)
            notag = True if notag == "true" else False
            mailed = request.query_params.get("mailed", None)
            mailed = True if mailed == "true" else False
            if request.method == 'GET':
                data = PatientFile.objects.filter(is_active=True)
                if patient_id:
                    data = data.filter(patient=patient_id)
                if practice_id:
                    data = data.filter(practice=practice_id)
                if tag:
                    data = data.filter(file_tags=tag)
                if notag:
                    data = data.filter(file_tags=None)
                if mailed:
                    data = data.filter(is_mailed=mailed)
                if upload_by:
                    data = data.filter(upload_by=upload_by)
                data = data.order_by('-id')
                page = self.paginate_queryset(data)
                if page is not None:
                    return self.get_paginated_response(PatientFileSerializer(page, many=True).data)
                return response.Ok(PatientFileSerializer(data, many=True).data)
        else:
            file_data = request.data.copy()
            result = []
            if type(file_data) == type(list()) and len(file_data) > 0:
                for file in file_data:
                    patient_id = file.get("patient", None)
                    if patient_id:
                        instance = Patients.objects.get(id=patient_id)
                        update_response = update_patient_extra_details(file, PatientFileSerializer, instance,
                                                                       PatientFile)
                        result.append(update_response)
            elif 'files' in file_data:
                req_data = request.data.copy()
                patient_id = req_data.get("patient", None)
                for file in file_data.pop('files', []):
                    req_data['file_type'] = file
                    instance = Patients.objects.get(id=patient_id)
                    update_response = update_patient_extra_details(req_data, PatientFileSerializer, instance,
                                                                   PatientFile)
                    result.append(update_response)
            else:
                patient_id = file_data.get("patient", None)
                file_id = file_data.pop("id", None)
                if patient_id:
                    if type(file_id) == type(list()) and len(file_id) > 0:
                        for file in file_id:
                            request.data["id"] = file
                            instance = Patients.objects.get(id=patient_id)
                            update_response = update_patient_extra_details(request, PatientFileSerializer, instance,
                                                                           PatientFile)
                            result.append(update_response)
                    else:
                        instance = Patients.objects.get(id=patient_id)
                        update_response = update_patient_extra_details(request, PatientFileSerializer, instance,
                                                                       PatientFile)
                        result.append(update_response)
            return response.Ok(result) if len(result) > 0 else response.BadRequest({'detail': 'Invalid data'})

    @action(methods=['GET'], detail=False)
    def copy_prescriptions(self, request, *args, **kwargs):
        prescription_id = request.query_params.get("id", None)
        practice = request.query_params.get("practice", None)
        if prescription_id:
            prescription_obj = PatientPrescriptions.objects.filter(is_active=True, id=prescription_id).first()
            if prescription_obj.practice.pk == int(practice):
                return response.Ok(PatientPrescriptionsDataSerializer(prescription_obj).data)
            else:
                prescription_res = PatientPrescriptionsDataSerializer(prescription_obj).data
                new_drugs = []
                for drug in prescription_obj.drugs.all():
                    practice_item = InventoryItem.objects.filter(name=drug.inventory.name, is_active=True,
                                                                 practice=practice).first()
                    drug_data = PatientInventorySerializer(drug).data
                    drug_data["inventory"] = InventoryItemSerializer(practice_item).data if practice_item else None
                    if practice_item:
                        new_drugs.append(drug_data)
                prescription_res["drugs"] = new_drugs
                return response.Ok(prescription_res)
        else:
            return response.BadRequest({"detail": "Invalid Prescription"})

    @action(methods=['GET', 'POST'], detail=False)
    def prescriptions(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        get_serializer = PatientPrescriptionsDataSerializer
        post_serializer = PatientPrescriptionsSerializer
        model = PatientPrescriptions
        sort_on = "-date"
        if request.method == 'GET':
            data = model.objects.filter(is_active=True)
            if patient_id:
                data = data.filter(patient=patient_id)
            if practice_id:
                data = data.filter(practice=practice_id)
            if sort_on:
                data = data.order_by(sort_on)
            page = self.paginate_queryset(data)
            if page is not None:
                return self.get_paginated_response(get_serializer(page, many=True).data)
            return response.Ok(get_serializer(data, many=True).data)
        else:
            if patient_id:
                patient_instance = Patients.objects.get(id=patient_id)
                print("instance:",patient_instance)
                update_response = update_patient_prescriptions(request, post_serializer, patient_instance, model)
                return response.Ok(update_response) if update_response else response.BadRequest(
                    {'detail': 'Send patient with data'})
            else:
                return response.BadRequest({'detail': 'Send patient with data'})

    @action(methods=['GET'], detail=False)
    def prescriptions_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    prescriptions_obj = PatientPrescriptions.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Prescription Exists"})
                practice = prescriptions_obj.practice.pk if prescriptions_obj.practice else None
                patient = prescriptions_obj.patient.pk if prescriptions_obj.patient else None
                patient_name = prescriptions_obj.patient.user.first_name \
                    if prescriptions_obj.patient and prescriptions_obj.patient.user \
                       and prescriptions_obj.patient.user.first_name else "User"
                doctor = prescriptions_obj.doctor.pk if prescriptions_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "PRESCRIPTION", PatientPrescriptions,
                                       PatientPrescriptionsDataSerializer, id, practice, patient, doctor,
                                       "prescriptions.html", "PrescriptionID")
                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "prescriptions")
                if "error" in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Prescription Id in Query Params'})

    @action(methods=['GET'], detail=False)
    def clinic_notes_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    clinic_notes_obj = PatientClinicNotes.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Clinical Notes Exists"})
                practice = clinic_notes_obj.practice.pk if clinic_notes_obj.practice else None
                patient = clinic_notes_obj.patient.pk if clinic_notes_obj.patient else None
                patient_name = clinic_notes_obj.patient.user.first_name if clinic_notes_obj.patient and clinic_notes_obj.patient.user else "User"
                doctor = clinic_notes_obj.doctor.pk if clinic_notes_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "CLINICAL NOTES", PatientClinicNotes,
                                       PatientClinicNotesDataSerializer, id, practice, patient, doctor,
                                       "clinical_notes.html", "ClinicNotesID")
                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "Clinical Notes")
                if 'error' in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Clinical Notes Id in Query Params'})

    @action(methods=['GET'], detail=False)
    def treatment_plan_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    treatment_plan_obj = PatientProcedure.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Clinical Notes Exists"})
                practice = treatment_plan_obj.practice.pk if treatment_plan_obj.practice else None
                patient = treatment_plan_obj.patient.pk if treatment_plan_obj.patient else None
                patient_name = treatment_plan_obj.patient.user.first_name if treatment_plan_obj.patient \
                                                                             and treatment_plan_obj.patient.user else "User"
                doctor = treatment_plan_obj.doctor.pk if treatment_plan_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "CLINICAL NOTES", PatientProcedure,
                                       PatientProcedureDataSerializer, id, practice, patient, doctor,
                                       "treatment_plan.html", "TreatmentPlanID")
                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "Treatment Plans")
                if "error" in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Treatment Plan Id in Query Params'})

    @action(methods=['GET'], detail=False)
    def medical_certificate_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                try:
                    medical_certificate_obj = MedicalCertificate.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Medical Certificate Exists"})
                practice = medical_certificate_obj.practice.pk if medical_certificate_obj.practice else None
                patient = medical_certificate_obj.patient.pk if medical_certificate_obj.patient else None
                doctor = medical_certificate_obj.doctor.pk if medical_certificate_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "MEDICAL LEAVE", MedicalCertificate,
                                       MedicalCertificateSerializer, id, practice, patient, doctor,
                                       "medical_certificate.html", "MedicalCertificateID")
                return response.Ok(GeneratedPdfSerializer(pdf_obj).data)
        else:
            return response.BadRequest({'detail': 'Send Medical Certificate Id in Query Params'})

    @action(methods=['GET'], detail=False)
    def lab_order_pdf(self, request, *args, **kwargs):
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    prescription_obj = PatientPrescriptions.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Lab Order Exists"})
                practice = prescription_obj.practice.pk if prescription_obj.practice else None
                patient = prescription_obj.patient.pk if prescription_obj.patient else None
                patient_name = prescription_obj.patient.user.first_name if prescription_obj.patient and prescription_obj.patient.user else "User"
                doctor = prescription_obj.doctor.pk if prescription_obj.doctor else None
                pdf_obj = generate_pdf("EMR", "LAB ORDER", PatientPrescriptions,
                                       PatientPrescriptionsDataSerializer, id, practice, patient, doctor,
                                       "lab_order.html", "LabOrderID")

                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "Lab Orders")
                if "error" in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Prescription Id in Query Params'})

    @action(methods=['GET'], detail=False)
    def unpaid_prescriptions(self, request, *args, **kwargs):
        patient_id = request.query_params.get("id", None)
        practice = request.query_params.get("practice", None)
        if patient_id:
            instance = Patients.objects.get(id=patient_id)
            if request.method == 'GET':
                prescriptions = PatientPrescriptions.objects.filter(patient=instance, is_active=True,
                                                                    #drugs__inventory__maintain_inventory=True,
                                                                    #drugs__is_billed=False
                                                                    )
                if practice:
                    prescriptions = prescriptions.filter(practice=practice)
                return response.Ok(PatientPrescriptionsDataSerializer(prescriptions.distinct('id'), many=True).data)
        else:
            return response.BadRequest({'detail': 'Send Patient Id in Query Params'})

    @action(methods=['GET', 'POST'], detail=False)
    def payment(self, request, *args, **kwargs):
        pratice_id = request.query_params.get("id", None)
        if pratice_id:
            instance = Patients.objects.get(id=pratice_id)
            if request.method == 'GET':
                return response.Ok(PatientPaymentSerializer(
                    PatientPayment.objects.filter(patient=instance, is_active=True), many=True).data)
            else:
                update_response = update_patient_extra_details(request, PatientPaymentSerializer, instance,
                                                               PatientPayment)
                return response.Ok(update_response) if update_response else response.BadRequest(
                    {'detail': 'Send id with data'})

        else:
            return response.BadRequest({'detail': 'Send Patient Id in Query Params'})

    @action(methods=['GET', 'POST'], detail=False)
    def medical_certificate(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        data = request.data.copy()
        get_serializer = MedicalCertificateSerializer
        post_serializer = MedicalCertificateSerializer
        model = MedicalCertificate
        sort_on = "-date"
        resp = common_function(self, request, patient_id, practice_id, get_serializer, post_serializer, model, sort_on)
        return resp

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def patient_notes(self, request, *args, **kwargs):
        if request.method == "GET":
            patient_id = request.query_params.get("patient", None)
        else:
            patient_id = request.data.get("patient", None)
        practice_id = request.query_params.get("practice", None)
        if request.method == 'GET':
            if patient_id:
                instance = PatientNotes.objects.filter(patient=patient_id, is_active=True)
                if practice_id:
                    instance = instance.filter(practice=practice_id)
                data = instance.order_by('-modified_at')
                page = self.paginate_queryset(data)
                if page is not None:
                    return self.get_paginated_response(PatientNotesDataSerializer(page, many=True).data)
                return response.Ok(PatientNotesDataSerializer(data, many=True).data)
            else:
                return response.BadRequest({'detail': 'Send Patient in Query Params'})
        else:
            data = request.data.copy()
            note_id = data.pop("id", None)
            user = request.user
            if user:
                staff = PracticeStaff.objects.filter(user=user).values('id').first()
                data["staff"] = staff["id"] if staff else None
            if note_id:
                note_obj = PatientNotes.objects.get(id=note_id)
                serializer = PatientNotesSerializer(instance=note_obj, data=data, partial=True)
            else:
                serializer = PatientNotesSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(
                PatientNotesSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def patient_notes_call(self, request, *args, **kwargs):
        if request.method == 'GET':
            patient_id = request.query_params.get("patient", None)
            meeting = request.query_params.get("meeting", None)
            practice = request.query_params.get("practice", None)
            call_type = request.query_params.get("type", None)
            if patient_id:
                instance = PatientCallNotes.objects.filter(patient=patient_id, is_active=True)
                if meeting:
                    instance = instance.filter(meeting=meeting)
                if call_type:
                    instance = instance.filter(type=call_type)
                if practice:
                    instance = instance.filter(practice=practice)
                data = instance.order_by('-modified_at')
                page = self.paginate_queryset(data)
                if page is not None:
                    return self.get_paginated_response(PatientCallNotesDetailSerializer(page, many=True).data)
                return response.Ok(PatientCallNotesDetailSerializer(data, many=True).data)
            else:
                return response.BadRequest({'detail': 'Send Patient in Query Params'})
        else:
            data = request.data.copy()
            mobile=request.data['mobile']
            patient = data.pop("patient", None)
            print('data',mobile,patient)
            try:
                if mobile:
                    patient = Patients.objects.get(is_active=True, user__mobile=mobile, user__is_active=True
                                                   )
                elif patient:
                    patient = Patients.objects.get(id=patient)
                else:
                    raise ValueError("Invalid Patient Mobile Number")
            except:
                return response.BadRequest({"detail": "Invalid patient mobile number"})
            data["patient"] = patient.pk
            note_id = data.pop("id", None)
            if note_id:
                note_obj = PatientCallNotes.objects.get(id=note_id)
                serializer = PatientCallNotesSerializer(instance=note_obj, data=data, partial=True)
            else:
                serializer = PatientCallNotesSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(
                PatientCallNotesSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Invalid data'})

    @action(methods=['GET'], detail=False)
    def mlm_report(self, request, *args, **kwargs):
        agents = request.query_params.get("agents", None)
        practice = request.query_params.get("practice", None)
        invoice = request.query_params.get("invoice", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        report_type = request.query_params.get("type", None)
        queryset = PatientWalletLedger.objects.filter(is_cancelled=False, is_mlm=True)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if agents:
            agent_list = agents.split(",")
            queryset = queryset.filter(patient__in=agent_list)
        if practice:
            queryset = queryset.filter(practice=practice)
        if invoice:
            queryset = queryset.filter(comments__icontains=invoice)
        if start and end:
            start_date = timezone.get_day_start(timezone.from_str(start))
            end_date = timezone.get_day_start(timezone.from_str(end))
            queryset = queryset.filter(created_at__range=[start_date, end_date])
        if report_type == "TRANSFER":
            data = queryset.values('ledger_type').annotate(total=Sum("amount"))
            queryset = queryset.order_by('-created_at')
            result = {"data": PatientWalletLedgerDataSerializer(queryset, many=True).data, "summary": data}
            if mail_to:
                for index, item in enumerate(PatientWalletLedgerDataSerializer(queryset, many=True).data):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Date": pd.to_datetime(item['created_at']).strftime(
                            '%B, %d, %Y, %H:%M %p') if 'created_at' in item and item['created_at'] else "--",
                        "Agent Name": item["patient"]["user"]["first_name"],
                        "Mobile Number": item["patient"]["user"]["mobile"],
                        "Email": item["patient"]["user"]["email"] if item["patient"]["user"]["email"] else "--",
                        "Gender": item["patient"]["gender"] if item["patient"]["gender"] else "--",
                        "Amount (INR)": item["amount"],
                        "Amount Type": item['amount_type'],
                        "Cr/Dr": item["ledger_type"],
                        "Margin": item["mlm"],
                        "Ledger Comment": item["comments"] if item["comments"] else "--"
                    })
                subject = "All MLM For " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "All_MLM__Report_" + start + "_" + end, mail_to,
                                          subject, body)
                result = {"detail": msg, "error": error}

            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        elif report_type == "MARGIN":
            data = queryset.exclude(mlm=None).values('mlm__margin__name') \
                .annotate(total=Sum('amount'), margin=F('mlm__margin__name')).values('margin', 'total').order_by(
                '-total')
            if mail_to:
                for index, item in enumerate(data):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Name": item["margin"],
                        "Total Amount": item["total"]
                    })
                subject = "Margin Type For " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Margin_Type__Report_" + start + "_" + end, mail_to,
                                          subject, body)
                data = {"detail": msg, "error": error}
            if "error" in data and data["error"]:
                return response.BadRequest(data)
            return response.Ok(data)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})

    @action(methods=['GET'], detail=False)
    def agent_wallet_balance(self, request, *args, **kwargs):
        agents = request.query_params.get("agents", None)
        practice = request.query_params.get("practice", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        queryset = PatientWallet.objects.filter(patient__is_agent=True, patient__is_active=True,
                                                patient__is_approved=True)
        print('queryset: %s' % queryset)
        if agents:
            agent_list = agents.split(",")
            queryset = queryset.filter(patient__in=agent_list)
        if practice:
            queryset = queryset.filter(patient__practice=practice)
        if mail_to:
            for index, item in enumerate(PatientWalletDataSerializer(queryset, many=True).data):
                ready_data.append({
                    "S. No.": index + 1,
                    "Agent Name": item["patient"]["user"]["first_name"],
                    "Mobile Number": item["patient"]["user"]["mobile"],
                    "Email": item["patient"]["user"]["email"] if item["patient"]["user"]["email"] else "--",
                    "Gender": item["patient"]["gender"] if item["patient"]["gender"] else "--",
                    "Refundable Amount": item['refundable_amount'],
                    "Non Refundable Amount": item['non_refundable']

                })
            subject = "Wallet Balance Amount Report for " + practice_name + " from " + start + " to " + end
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Wallet_Balance_Amount_Report_" + start + "_" + end, mail_to,
                                      subject, body)
            queryset = {"detail": msg, "error": error}
            return response.Ok(queryset)
        if "error" in queryset and queryset["error"]:
            return response.BadRequest(queryset)

        return response.Ok(PatientWalletDataSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=False)
    def app_summary(self, request, *args, **kwargs):
        practice = request.query_params.get("practice", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        if not start or not end:
            return response.BadRequest({"detail": "Invalid Dates Selected"})
        if not practice:
            return response.BadRequest({"detail": "Invalid Practice Selected"})
        output = generate_app_report(practice, start, end)
        return response.Ok(output)

    @action(methods=['GET'], detail=False)
    def cron_test(self, request, *args, **kwargs):
        data = appointment_summary()
        return response.Ok(data)

    @action(methods=['GET'], detail=True)
    def advance_payment(self, request, *args, **kwargs):
        patient = self.get_object()
        practice = request.query_params.get("practice_id", None)
        queryset = PatientPayment.objects.filter(patient=patient, is_cancelled=False, is_active=True, is_advance=True)
        if practice:
            queryset = queryset.filter(practice=practice)
        total = queryset.values('patient').annotate(sum=Sum('advance_value'))
        total_value = total[0]['sum'] if len(total) > 0 and 'sum' in total[0] else 0
        return response.Ok({"data": PatientPaymentSerializer(queryset, many=True).data, "max_allowed": total_value})

    @action(methods=['GET'], detail=False)
    def print(self, request, *args, **kwargs):
        page_settings = request.query_params
        logo_include = page_settings.get("logo_include", None)
        logo_path = page_settings.get("logo_path", None)
        logo_url = page_settings.get("logo_url", None)
        type = page_settings.get("type", None)
        sub_type = page_settings.get("sub_type", None)
        practice = page_settings.get("practice", None)
        pdf = page_settings.get("pdf", None)

        logo = ''
        model_data = {'date': '2019-10-01T09:30:00Z'}
        template_name = "vital_signs.html"
        name = "IgnoreDemo"
        if logo_include:
            logo = logo_path
            if logo:
                pngFile = open(os.path.join(settings.BASE_DIR, 'media', logo), 'rb')
                logo = base64.b64encode(pngFile.read()).decode('ascii')
        elif logo_url:
            logo = logo_url
        patient_data = CONST_PATIENT_DATA
        doctor_data = CONST_DOCTOR_DATA
        practice_data = PracticeSerializer(Practice.objects.get(id=practice)).data if practice else CONST_PRACTICE_DATA
        if type == "EMR" and sub_type == "REPORT MANUAL":
            template_name = "vital_signs.html"
            name = "VitalSignDemo"
            model_data = CONST_VITAL_SIGN_DATA
        elif type == "EMR" and sub_type == "MEDICAL LEAVE":
            template_name = "medical_certificate.html"
            name = "MedicalCertificateDemo"
            model_data = CONST_MEDICAL_LEAVE_DATA
        elif type == "EMR" and sub_type == "CLINICAL NOTES":
            template_name = "clinical_notes.html"
            name = "ClinicalNotesDemo"
            model_data = CONST_CLINICAL_NOTES_DATA
        elif type == "EMR" and sub_type == "TREATMENT PLAN":
            template_name = "treatment_plan.html"
            name = "TreatmentPlanDemo"
            model_data = CONST_TREATMENT_PLAN_DATA
        elif type == "EMR" and sub_type == "PRESCRIPTION":
            template_name = "prescriptions.html"
            name = "PrescriptionDemo"
            model_data = CONST_PRESCRIPTION_DATA
        elif type == "BILLING" and sub_type == "RECEIPTS":
            name = "ReceiptsDemo"
            template_name = "payment.html"
            model_data = CONST_PAYMENTS_DATA
        elif type == "BILLING" and sub_type == "BOOKING":
            name = "ReceiptsDemo"
            template_name = "booking.html"
            model_data = CONST_BOOKING_DATA
        elif type == "BILLING" and sub_type == "RETURN":
            name = "ReturnDemo"
            template_name = "return.html"
            model_data = CONST_RETURN_DATA
        elif type == "BILLING" and sub_type == "INVOICE":
            name = "InvoiceDemo"
            template_name = "invoice.html"
            model_data = CONST_INVOICE_DATA
        elif type == "BILLING" and sub_type == "PROFORMA":
            name = "ProformaDemo"
            template_name = "proforma_invoice.html"
            model_data = CONST_INVOICE_DATA
        elif type == "EMR" and sub_type == "LAB ORDER":
            name = "LabOrderDemo"
            template_name = "lab_order.html"
            model_data = CONST_LAB_ORDER_DATA
        elif type == "EMR" and sub_type == "CASE SHEET":
            name = "CaseSheetDemo"
            template_name = "case_sheet.html"
            model_data = CONST_CASE_SHEET_DATA
        elif type == "APPOINTMENT" and sub_type == "CREATE":
            name = "AppointmentConfirmation"
            template_name = "appointment_email/appointment_confirmation.html"
            model_data = CONST_APPOINTMENT_DATA
        elif type == "APPOINTMENT" and sub_type == "CANCEL":
            name = "AppointmentCancellation"
            template_name = "appointment_email/appointment_cancellation.html"
            model_data = CONST_APPOINTMENT_DATA
        elif type == "APPOINTMENT" and sub_type == "FOLLOWUP":
            name = "AppointmentFollowUP"
            template_name = "appointment_email/appointment_followup.html"
            model_data = CONST_APPOINTMENT_DATA
        elif type == "APPOINTMENT" and sub_type == "REMINDER":
            name = "AppointmentReminder"
            template_name = "appointment_email/appointment_reminder.html"
            model_data = CONST_APPOINTMENT_DATA
        elif type == "GREETING" and sub_type == "ANNIVERSARY":
            name = "PatientAnniversary"
            template_name = "patient_greeting_email/anniversary.html"
            model_data = CONST_PATIENT_DATA
        elif type == "GREETING" and sub_type == "BIRTHDAY":
            name = "PatientBirthday"
            template_name = "patient_greeting_email/birthday.html"
            model_data = CONST_PATIENT_DATA
        if practice:
            model_data["practice_data"] = practice_data
        data = {
            'logo': logo,
            'page_settings': page_settings,
            'data': model_data,
            'patient': patient_data,
            'doctor': doctor_data,
            'practice': practice_data
        }

        if pdf:
            template = get_template(template_name)
            pdf = pdf_document.html_to_pdf_convert(template, data)
            if id:
                pdf_obj, flag = GeneratedPdf.objects.get_or_create(name=name)
                pdf_obj.report.save("%s-%s.pdf" % (pdf_obj.uuid, "DEMO"), pdf)
            else:
                pdf_obj, flag = GeneratedPdf.objects.get_or_create(name=name)
                pdf_obj.report.save("%s-%s.pdf" % (pdf_obj.uuid, "DEMO"), pdf)
            if not settings.SERVER == "PRODUCTION":
                pdf.flush()
            return response.Ok(GeneratedPdfSerializer(pdf_obj).data)
        else:
            return render(request, template_name, data)

    @action(methods=['GET'], detail=True)
    def ledger(self, request, *args, **kwargs):
        practice = request.query_params.get("practice_id", None)
        patient = self.get_object()
        invoices = PatientInvoices.objects.filter(patient=patient, is_active=True, is_cancelled=False)
        payments = PatientPayment.objects.filter(patient=patient, is_active=True, is_cancelled=False)
        returns = ReturnPayment.objects.filter(patient=patient, is_active=True, is_cancelled=False)
        if practice:
            invoices = invoices.filter(practice=practice)
            payments = payments.filter(practice=practice)
            returns = returns.filter(practice=practice)
        invoices_data = PatientInvoicesDataSerializer(invoices, many=True).data
        payments_data = PatientPaymentDataSerializer(payments, many=True).data
        returns_data = ReturnPaymentSerializer(returns, many=True).data

        def weighted(data):
            if data:
                return pd.to_datetime(data)
            else:
                return datetime.today()

        data = [dict(**x, **{"ledger_type": "Invoice"}) for x in invoices_data] + [
            dict(**x, **{"ledger_type": "Payment"}) for x in payments_data] + [dict(**x, **{"ledger_type": "Return"})
                                                                               for x in returns_data]
        data = sorted(data, key=lambda x: weighted(x["date"]))
        return response.Ok(data)

class SearchMedicanViewSet(ModelViewSet):
    serializer_class = PatientAllopathicMedicinesSerializer
    queryset = PatientAllopathicMedicines.objects.all()
    permission_classes = (PatientsPermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    def get_queryset(self):
        queryset = super(SearchMedicanViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        name = self.request.query_params.get("name", None)
        if name:
            queryset=PatientAllopathicMedicines.objects.filter(name__icontains=name)
        return queryset
    
    def create(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    def update(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})
    

class SymptomsViewSet(ModelViewSet):
    serializer_class = SymptomListSerializer
    queryset = SymptomList.objects.all()
    permission_classes = (PatientsPermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    def get_queryset(self):
        queryset = super(SymptomsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        name = self.request.query_params.get("name", None)
        if name:
            queryset=SymptomList.objects.filter(name__icontains=name)
        return queryset
    
    def create(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    def update(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})
    

class DiseasesViewSet(ModelViewSet):
    serializer_class = DiseaseListSerializer
    queryset = DiseaseList.objects.all()
    permission_classes = (PatientsPermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    def get_queryset(self):
        queryset = super(DiseasesViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        name = self.request.query_params.get("name", None)
        if name:
            queryset=DiseaseList.objects.filter(name__icontains=name)
        return queryset

        
    def create(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    def update(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})
    
    
class PatientProfileViewSet(ModelViewSet):
    serializer_class = PatientsDetailsSerializer
    queryset = Patients.objects.all()
    permission_classes = (PatientsPermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    def get_queryset(self):
        queryset = super(PatientProfileViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
    
    def list(self,request,*args,**kwargs):
        return response.MethodNotAllowed({"detail": "This method is not allowed."})
        
    def create(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    # def update(self, request, *args, **kwargs):
    #     return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})
    
class ServiceViewSet(ModelViewSet):
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()
    permission_classes = (BlogImagePermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    def get_queryset(self):
        queryset = super(ServiceViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
        
    # def create(self, request, *args, **kwargs):
    #     return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    def update(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})
    


class PatientManualReportViewSet(ModelViewSet):
    serializer_class = PatientManualReportSerializer
    queryset = PatientManualReport.objects.all()
    permission_classes = (BlogImagePermissions,)
    parser_classes = (JSONParser, XMLParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    
    # def get_queryset(self):
    #     queryset = super(PatientManualReportViewSet, self).get_queryset()
    #     queryset = queryset.filter(is_active=True)
    #     return queryset
        
    # def create(self, request, *args, **kwargs):
    #     return response.MethodNotAllowed({"detail": "POST method is not allowed."})
    
    # def update(self, request, *args, **kwargs):
    #     return response.MethodNotAllowed({"detail": "PUT method is not allowed."})
    
    
    def destroy(self, request, *args, **kwargs):
        return response.MethodNotAllowed({"detail": "Delete method is not allowed."})