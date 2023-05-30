import json
from datetime import datetime, timedelta

from ..accounts.models import Role, User
from ..accounts.serializers import RoleSerializer
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..billing.serializers import ReservationsStaffSerializer, ReservationsSerializer, \
    ReservationsDataSerializer
from ..constants import CONST_GLOBAL_PRACTICE, ROLES_PERMISSIONS
from ..logger_constants import CONST_LOG_GENERATOR
from ..patients.serializers import GeneratedPdfSerializer, PatientsBasicDataSerializer
from ..patients.services import get_invoice_report, get_payment_report, get_patients_report, get_expense_report, \
    generate_pdf, mail_file
from .models import Practice, PracticeCalenderSettings, ProcedureCatalog, Taxes, PaymentModes, \
    PracticeOffers, PracticeComplaints, Observations, Diagnoses, Investigations, Treatmentnotes, \
    Filetags, PracticeStaff, Communications, EmailCommunications, LabPanel, LabTestCatalog, Registration, \
    DrugCatalog, ExpenseType, AppointmentCategory, Vendor, Expenses, ActivityLog, DrugType, DrugUnit, \
    PracticeUserPermissions, PracticePrintSettings, PrescriptionTemplate, RoomTypeSettings, VisitingTime, Membership, \
    PracticeVitalSign, PracticeStaffRelation, MedicineBookingPackage, BedBookingPackage, OtherDiseases, Medication, \
    PushNotifications, PermissionGroup,NoticeBoard
from .permissions import PracticePermissions as PracticeClientPermissions, PracticeStaffPermissions, \
    VendorPermissions, ExpensesPermissions, ActivityLogPermissions, DrugTypePermissions, DrugUnitPermissions, \
    PracticeUserPermissionsPermissions
from .serializers import PracticeSerializer, PracticeCalenderSettingsSerializer, \
    AppointmentCategorySerializer, ProcedureCatalogSerializer, ProcedureCatalogDataSerializer, TaxesSerializer, \
    PaymentModesSerializer, PracticeOffersSerializer, PracticeComplaintsSerializer, PracticeStaffBasicSerializer, \
    ObservationsSerializer, DiagnosesSerializer, InvestigationsSerializer, TreatmentnotesSerializer, FiletagsSerializer, \
    PracticeStaffSerializer, PrescriptionTemplateDataSerializer, RoomTypeSettingsSerializer, PracticeBasicSerializer, \
    CommunicationsSerializer, LabTestCatalogSerializer, LabPanelSerializer, DrugCatalogSerializer, \
    ExpenseTypeSerializer, VendorSerializer, ExpensesSerializer, ActivityLogSerializer, DrugTypeSerializer, \
    DrugUnitSerializer, PracticeUserPermissionsSerializer, ExpensesDataSerializer, PracticePrintSettingsSerializer, \
    MembershipSerializer, LabPanelDataSerializer, EmailCommunicationsSerializer, VisitingTimeSerializer, \
    VisitingTimeDataSerializer, PracticeVitalSignSerializer, PracticeStaffRelationSerializer, \
    PracticeStaffRelationDataSerializer, MedicineBookingPackageSerializer, BedBookingPackageSerializer, \
    BedBookingPackageDataSerializer, MedicineBookingPackageDataSerializer, OtherDiseasesSerializer, \
    MedicationSerializer, PushNotificationSerializer, PushNotificationSaveSerializer, RegistrationSerializer, \
    PermissionGroupSerializer,NoticeBoardSerializer
from .services import update_pratice_related_object, get_appoinment_report, seat_availability, \
    update_pratice_related_calender_object, update_pratice_related_drug_object, update_prescription_template, \
    payment_capture, get_emr_report, dict_to_mail
from ..utils import timezone
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncMonth as Month, TruncYear as Year, TruncDay as Day
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class PracticeViewSet(ModelViewSet):
    serializer_class = PracticeSerializer
    queryset = Practice.objects.all()
    permission_classes = (PracticeClientPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(PracticeViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        medicine = self.request.query_params.get("medicine", None)
        bed_booking = self.request.query_params.get("bed_booking", None)
        if medicine and medicine == "true":
            practices = MedicineBookingPackage.objects.filter(is_active=True).values_list('practice', flat=True)
            queryset = queryset.filter(id__in=practices)
        if bed_booking and bed_booking == "true":
            practices = BedBookingPackage.objects.filter(is_active=True).values_list('practice', flat=True)
            queryset = queryset.filter(id__in=practices)
        return queryset.order_by('-id')

    @action(methods=['POST'], detail=False)
    def payment(self, request, *args, **kwargs):
        data = request.data.copy()
        payment_id = data.get("payment_id", None)
        amount = data.get("amount", None)
        result = payment_capture(payment_id, float(amount))
        if not result.get("error", None):
            return response.Ok(result)
        else:
            return response.BadRequest(result)

    @action(methods=['POST'], detail=True)
    def delete_clinic(self, request, *args, **kwargs):
        # Here we get all the practice
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return_dict = {"suceess": "Clinic deleted Successfully", }
        return response.Ok(return_dict)

    @action(methods=['GET', 'POST'], detail=True)
    def calender_settings(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(PracticeCalenderSettingsSerializer(
                instance.practicecalendersettings_set.filter(is_active=True).order_by('-modified_at'), many=True).data)
        else:
            update_response = update_pratice_related_calender_object(request, PracticeCalenderSettingsSerializer,
                                                                     instance, PracticeCalenderSettings)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def doctor_timing(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            doctor_str = request.query_params.get("doctor", None)
            data = VisitingTime.objects.filter(is_active=True, practice=instance.pk)
            if doctor_str:
                doctors = doctor_str.split(",")
                data = data.filter(doctor__in=doctors)
            return response.Ok(VisitingTimeDataSerializer(data.order_by('-modified_at'), many=True).data)
        else:
            update_response = update_pratice_related_calender_object(request, VisitingTimeSerializer, instance,
                                                                     VisitingTime)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def appointment_category(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                AppointmentCategorySerializer(AppointmentCategory.objects.filter(is_active=True), many=True).data)
        else:
            update_response = update_pratice_related_object(request, AppointmentCategorySerializer, instance,
                                                            AppointmentCategory)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def vital_sign(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                PracticeVitalSignSerializer(PracticeVitalSign.objects.filter(is_active=True, practice=instance.pk),
                                            many=True).data)
        else:
            update_response = update_pratice_related_object(request, PracticeVitalSignSerializer, instance,
                                                            PracticeVitalSign)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET'], detail=True)
    def practice_staff(self, request, *args, **kwargs):
        response_dict = {
            "doctors": [],
            "staff": []
        }
        all = request.query_params.get("all", None)
        role = request.query_params.get("role", None)
        all = True if all == "true" else False
        this_practice = []
        instance = self.get_object()
        practice = instance.pk
        all_staff = PracticeStaff.objects.filter(is_active=True)
        if role:
            all_staff = all_staff.filter(role=role)
        staff_data = PracticeStaffSerializer(all_staff.order_by('-id'), many=True).data
        for staff in staff_data:
            count = PracticeStaffRelation.objects.filter(is_active=True, practice=practice,
                                                         staff=staff["id"]).count()
            if count > 0:
                staff["in_practice"] = True
                this_practice.append(staff)
            else:
                staff["in_practice"] = False
        if all:
            response_dict.update({'staff': staff_data})
        else:
            response_dict.update({'staff': this_practice})
        return response.Ok(response_dict)

    @action(methods=['GET', 'POST'], detail=True, pagination_class=StandardResultsSetPagination)
    def procedure_category(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            name = request.query_params.get("name", None)
            pagination = request.query_params.get("pagination", None)
            pagination = False if pagination == "false" else True
            data = ProcedureCatalog.objects.filter(practice=instance, is_active=True)
            if name:
                data = data.filter(name__icontains=name)
            data = data.order_by('-id')
            page = self.paginate_queryset(data)
            if pagination and page is not None:
                return self.get_paginated_response(ProcedureCatalogDataSerializer(page, many=True).data)
            return response.Ok(ProcedureCatalogDataSerializer(data, many=True).data)
        else:
            update_response = update_pratice_related_object(request, ProcedureCatalogSerializer, instance,
                                                            ProcedureCatalog)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def taxes(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(TaxesSerializer(Taxes.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                               many=True).data)
        else:
            update_response = update_pratice_related_object(request, TaxesSerializer, instance, Taxes)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def payment_modes(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                PaymentModesSerializer(PaymentModes.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                       many=True).data)
        else:
            update_response = update_pratice_related_object(request, PaymentModesSerializer, instance, PaymentModes)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def communications(self, request, *args, **kwargs):
        instance = self.get_object()
        language = request.query_params.get("language", None)
        if request.method == 'GET':
            queryset = Communications.objects.filter(practice=instance, is_active=True)
            if language:
                queryset = queryset.filter(sms_language=language)
            return response.Ok(CommunicationsSerializer(queryset.order_by('id').last()).data)
        else:
            update_response = update_pratice_related_object(request, CommunicationsSerializer, instance, Communications)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def email_communications(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(EmailCommunicationsSerializer(
                EmailCommunications.objects.filter(practice=instance, is_active=True).order_by('-id'), many=True).data)
        else:
            update_response = update_pratice_related_object(request, EmailCommunicationsSerializer, instance,
                                                            EmailCommunications)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def practice_print_settings(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            type = request.query_params.get('type', None)
            sub_type = request.query_params.get('sub_type', None)
            if type and sub_type:
                return response.Ok((PracticePrintSettingsSerializer(
                    PracticePrintSettings.objects.filter(practice=instance, is_active=True, type=type,
                                                         sub_type=sub_type), many=True).data))
            else:
                return response.Ok((PracticePrintSettingsSerializer(
                    PracticePrintSettings.objects.filter(practice=instance, is_active=True), many=True).data))
        else:
            update_response = update_pratice_related_object(request, PracticePrintSettingsSerializer, instance,
                                                            PracticePrintSettings)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True, pagination_class=StandardResultsSetPagination)
    def labtest(self, request, *args, **kwargs):
        instance = self.get_object()
        name = request.query_params.get("name", None)
        if request.method == 'GET':
            queryset = LabTestCatalog.objects.filter(practice=instance, is_active=True)
            if name:
                queryset = queryset.filter(name__icontains=name)
            queryset = queryset.order_by('-id')
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(LabTestCatalogSerializer(page, many=True).data)
            return response.Ok(LabTestCatalogSerializer(queryset, many=True).data)
        else:
            update_response = update_pratice_related_object(request, LabTestCatalogSerializer, instance, LabTestCatalog)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def labpanel(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                LabPanelDataSerializer(LabPanel.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                       many=True).data)
        else:
            update_response = update_pratice_related_object(request, LabPanelSerializer, instance, LabPanel)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def drugtype(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                DrugTypeSerializer(DrugType.objects.filter(practice=instance, is_active=True), many=True).data)
        else:
            update_response = update_pratice_related_drug_object(request, DrugTypeSerializer, instance, DrugType)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def drugunit(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                (DrugUnitSerializer(DrugUnit.objects.filter(practice=instance, is_active=True), many=True).data))
        else:
            update_response = update_pratice_related_drug_object(request, DrugUnitSerializer, instance, DrugUnit)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def drugcatalog(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            deleted = request.query_params.get("deleted", None)
            if deleted:
                return response.Ok((DrugCatalogSerializer(
                    DrugCatalog.objects.filter(practice=instance, is_active=False), many=True).data))
            else:
                return response.Ok((DrugCatalogSerializer(DrugCatalog.objects.filter(practice=instance, is_active=True),
                                                          many=True).data))
        else:
            update_response = update_pratice_related_drug_object(request, DrugCatalogSerializer, instance, DrugCatalog)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def expense_type(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            deleted = request.query_params.get("deleted", None)
            if deleted:
                return response.Ok(ExpenseTypeSerializer(
                    ExpenseType.objects.filter(practice=instance, is_active=False).order_by('-id'), many=True).data)
            else:
                return response.Ok(
                    ExpenseTypeSerializer(ExpenseType.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                          many=True).data)
        else:
            update_response = update_pratice_related_object(request, ExpenseTypeSerializer, instance, ExpenseType)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=False)
    def membership(self, request, *args, **kwargs):
        if request.method == 'GET':
            deleted = request.query_params.get("deleted", None)
            if deleted:
                return response.Ok(MembershipSerializer(
                    Membership.objects.filter(is_active=False).order_by('-id'), many=True).data)
            else:
                return response.Ok(
                    MembershipSerializer(Membership.objects.filter(is_active=True).order_by('-id'), many=True).data)
        else:
            new_data_request = request.data.copy()
            membership_id = new_data_request.pop("id", None)
            if membership_id:
                membership_obj = Membership.objects.filter(id=membership_id).first()
                serializer = MembershipSerializer(instance=membership_obj, data=new_data_request, partial=True)
            else:
                serializer = MembershipSerializer(data=new_data_request, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(MembershipSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=False)
    def registration(self, request, *args, **kwargs):
        if request.method == 'GET':
            deleted = request.query_params.get("deleted", None)
            if deleted:
                return response.Ok(RegistrationSerializer(
                    Registration.objects.filter(is_active=False).order_by('-id'), many=True).data)
            else:
                return response.Ok(
                    RegistrationSerializer(Registration.objects.filter(is_active=True).order_by('-id'), many=True).data)
        else:
            new_data_request = request.data.copy()
            registration_id = new_data_request.pop("id", None)
            if registration_id:
                registration_obj = Registration.objects.filter(id=registration_id).first()
                serializer = RegistrationSerializer(instance=registration_obj, data=new_data_request, partial=True)
            else:
                serializer = RegistrationSerializer(data=new_data_request, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(
                RegistrationSerializer(update_response).data) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def offers(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(PracticeOffersSerializer(
                PracticeOffers.objects.filter(practice=instance, is_active=True).order_by('-id'), many=True).data)
        else:
            update_response = update_pratice_related_object(request, PracticeOffersSerializer, instance, PracticeOffers)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def complaints(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(PracticeComplaintsSerializer(
                PracticeComplaints.objects.filter(practice=instance, is_active=True).order_by('-id'), many=True).data)
        else:
            update_response = update_pratice_related_object(request, PracticeComplaintsSerializer, instance,
                                                            PracticeComplaints)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def observations(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                ObservationsSerializer(Observations.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                       many=True).data)
        else:
            update_response = update_pratice_related_object(request, ObservationsSerializer, instance, Observations)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def diagnoses(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                DiagnosesSerializer(Diagnoses.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                    many=True).data)
        else:
            update_response = update_pratice_related_object(request, DiagnosesSerializer, instance, Diagnoses)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def investigations(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok((InvestigationsSerializer(
                Investigations.objects.filter(practice=instance, is_active=True).order_by('-id'), many=True).data))
        else:
            update_response = update_pratice_related_object(request, InvestigationsSerializer, instance, Investigations)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def treatmentnotes(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok((TreatmentnotesSerializer(
                Treatmentnotes.objects.filter(practice=instance, is_active=True).order_by('-id'), many=True).data))
        else:
            update_response = update_pratice_related_object(request, TreatmentnotesSerializer, instance, Treatmentnotes)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def filetags(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                FiletagsSerializer(Filetags.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                   many=True).data)
        else:
            update_response = update_pratice_related_object(request, FiletagsSerializer, instance, Filetags)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def medication(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                MedicationSerializer(Medication.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                     many=True).data)
        else:
            update_response = update_pratice_related_object(request, MedicationSerializer, instance, Medication)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET'], detail=True, pagination_class=StandardResultsSetPagination)
    def emr_report(self, request, *args, **kwargs):
        instance = self.get_object()
        resp = get_emr_report(instance, request)
        if "error" in resp and resp["error"]:
            return response.BadRequest(resp)
        return response.Ok(resp)

    @action(methods=['GET'], detail=True)
    def appointment_report(self, request, *args, **kwargs):
        instance = self.get_object()
        result = get_appoinment_report(instance, request)
        if result["error"]:
            return response.BadRequest(result)
        return response.Ok(result)

    @action(methods=['GET', 'POST'], detail=True, pagination_class=StandardResultsSetPagination)
    def prescription_template(self, request, *args, **kwargs):
        instance = self.get_object()
        name = request.query_params.get("name", None)
        if request.method == 'GET':
            queryset = PrescriptionTemplate.objects.filter(practice=instance, is_active=True)
            if name:
                queryset = queryset.filter(name__icontains=name)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(PrescriptionTemplateDataSerializer(page, many=True).data)
            return response.Ok(PrescriptionTemplateDataSerializer(queryset, many=True).data)
        else:
            return response.Ok(update_prescription_template(instance, request))

    @action(methods=['GET'], detail=False)
    def user_permissions(self, request, *args, **kwargs):
        staff = request.query_params.get('staff', None)
        if staff:
            practices = PracticeBasicSerializer(Practice.objects.filter(is_active=True), many=True).data
            all_permissions = ROLES_PERMISSIONS
            allowed_permissions = PracticeUserPermissionsSerializer(
                PracticeUserPermissions.objects.exclude(practice=None).filter(staff=staff, is_active=True),
                many=True).data
            return response.Ok({"practices": practices,
                                "all_permissions": all_permissions,
                                "allowed_permissions": allowed_permissions
                                })
        else:
            return response.BadRequest({"detail": "Please select a Staff"})

    @action(methods=['GET'], detail=True)
    def invoice_report(self, request, *args, **kwargs):
        instance = self.get_object()
        return response.Ok(get_invoice_report(instance, request))

    @action(methods=['GET'], detail=True)
    def payments_report(self, request, *args, **kwargs):
        instance = self.get_object()
        return response.Ok(get_payment_report(instance, request))

    @action(methods=['GET'], detail=True)
    def patients_report(self, request, *args, **kwargs):
        instance = self.get_object()
        return response.Ok(get_patients_report(instance, request))

    @action(methods=['GET'], detail=True)
    def expense_report(self, request, *args, **kwargs):
        instance = self.get_object()
        return response.Ok(get_expense_report(instance, request))

    @action(methods=['GET', 'POST'], detail=True)
    def vendor(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.method == 'GET':
            return response.Ok(
                VendorSerializer(Vendor.objects.filter(practice=instance, is_active=True).order_by('-id'),
                                 many=True).data)
        else:
            update_response = update_pratice_related_object(request, VendorSerializer, instance, Vendor)
            return response.Ok(update_response) if update_response else response.BadRequest(
                {'detail': 'Send id with data'})

    @action(methods=['GET', 'POST'], detail=True)
    def room_types(self, request, *args, **kwargs):
        practice = self.get_object()
        if request.method == 'GET':
            data = RoomTypeSettings.objects.filter(is_active=True)
            if practice:
                data = data.filter(practice=practice)
            return response.Ok(RoomTypeSettingsSerializer(data.order_by('-id'), many=True).data)
        else:
            data = request.data.copy()
            room_id = data.pop("id", None)
            data["practice"] = practice.pk
            if room_id:
                room_obj = RoomTypeSettings.objects.get(id=room_id)
                serializer = RoomTypeSettingsSerializer(instance=room_obj, data=data, partial=True)
            else:
                serializer = RoomTypeSettingsSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(RoomTypeSettingsSerializer(instance=update_response).data)

    @action(methods=['GET', 'POST'], detail=True)
    def medicine_packages(self, request, *args, **kwargs):
        practice = self.get_object()
        if request.method == 'GET':
            data = MedicineBookingPackage.objects.filter(is_active=True)
            if practice:
                data = data.filter(practice=practice)
            return response.Ok(MedicineBookingPackageDataSerializer(data.order_by('-id'), many=True).data)
        else:
            data = request.data.copy()
            data["practice"] = practice.pk
            medicine_id = data.pop("id", None)
            price = data["price"] if "price" in data and data["price"] else 0
            tax_percent = self.calculate_tax(data["taxes"])
            tax_div = 1 + (tax_percent / 100)
            data["price"] = price / tax_div
            data["tax_value"] = data["price"] * tax_percent / 100
            if medicine_id:
                medicine_obj = MedicineBookingPackage.objects.get(id=medicine_id)
                medicine_obj.is_active = False
                medicine_obj.save()
            serializer = MedicineBookingPackageSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(MedicineBookingPackageSerializer(instance=update_response).data)

    @action(methods=['GET'], detail=True)
    def booking_pdf(self, request, *args, **kwargs):
        from ..patients.models import Reservations
        id = request.query_params.get("id", None)
        if id:
            if request.method == 'GET':
                mail_to = request.query_params.get("mail_to", None)
                try:
                    reservation_obj = Reservations.objects.get(id=id)
                except:
                    return response.BadRequest({"detail": "No Such Reservation Exists"})
                practice = reservation_obj.practice.pk if reservation_obj.practice else None
                patient = reservation_obj.patient.pk if reservation_obj.patient else None
                patient_name = reservation_obj.patient.user.first_name if reservation_obj.patient and reservation_obj.patient.user else "User"
                pdf_obj = generate_pdf("BILLING", "BOOKING", Reservations, ReservationsDataSerializer, id,
                                       practice, patient, None, "booking.html", "BookingID")
                result = GeneratedPdfSerializer(pdf_obj).data
                if mail_to:
                    result = mail_file(patient_name, mail_to, pdf_obj, practice, "Booking")
                if "error" in result and result["error"]:
                    return response.BadRequest(result)
                return response.Ok(result)
        else:
            return response.BadRequest({'detail': 'Send Booking Id in Query Params'})

    @action(methods=['GET', 'POST'], detail=True)
    def bed_packages(self, request, *args, **kwargs):
        practice = self.get_object()
        if request.method == 'GET':
            data = BedBookingPackage.objects.filter(is_active=True)
            if practice:
                data = data.filter(practice=practice)
            return response.Ok(BedBookingPackageDataSerializer(data.order_by('-id'), many=True).data)
        else:
            data = request.data.copy()
            data["practice"] = practice.pk
            room_id = data.pop("id", None)
            tax_percent = self.calculate_tax(data["taxes"])
            tax_div = 1 + (tax_percent / 100)
            normal_price = data["normal_price"] if "normal_price" in data and data["normal_price"] else 0
            tatkal_price = data["tatkal_price"] if "tatkal_price" in data and data["tatkal_price"] else 0
            data["normal_price"] = float(normal_price) / tax_div
            data["tatkal_price"] = float(tatkal_price) / tax_div
            data["normal_tax_value"] = float(data["normal_price"]) * tax_percent / 100
            data["tatkal_tax_value"] = float(data["tatkal_price"]) * tax_percent / 100
            if room_id:
                room_obj = BedBookingPackage.objects.get(id=room_id)
                serializer = BedBookingPackageSerializer(instance=room_obj, data=data, partial=True)
            else:
                serializer = BedBookingPackageSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(BedBookingPackageSerializer(instance=update_response).data)

    def calculate_tax(self, taxes):
        tax_percent = 0.0
        for tax in taxes:
            tax_data = Taxes.objects.get(id=tax)
            tax_percent += tax_data.tax_value if tax_data else 0
        return tax_percent

    @action(methods=['GET'], detail=True)
    def seat_availability(self, request, *args, **kwargs):
        from ..patients.models import Reservations
        Reservations.objects.filter(payment_status="PENDING",
                                    modified_at__lte=datetime.now() - timedelta(minutes=15)).update(
            payment_status="FAILED")
        practice = self.get_object()
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        bed_package = request.query_params.get('bed_package', None)
        result = seat_availability(practice, start, end, bed_package)
        return response.BadRequest(result) if "detail" in result else response.Ok(result)

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def seat_booking_report(self, request, *args, **kwargs):
        from ..patients.models import Reservations
        Reservations.objects.filter(payment_status="PENDING",
                                    modified_at__lte=datetime.now() - timedelta(minutes=15)).update(
            payment_status="FAILED")
        practice = request.query_params.get("practice", None)
        patients = request.query_params.get("patients", None)
        type = request.query_params.get("type", None)
        report_type = request.query_params.get("report_type", None)
        bed_packages = request.query_params.get("bed_packages", None)
        start = request.query_params.get("start", None)
        end = request.query_params.get("end", None)
        payment_status = request.query_params.get("payment_status", "PENDING,SUCCESSFUL,FAILED,CANCELLED")
        queryset = Reservations.objects.filter(payment_status__in=payment_status.split(","))
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if patients:
            queryset = queryset.filter(patient__in=patients.split(","))
        if practice:
            queryset = queryset.filter(practice=practice)
            instance = Practice.objects.filter(id=practice).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if bed_packages:
            queryset = queryset.filter(bed_package__in=bed_packages.split(","))
        if type == "OPD":
            queryset = queryset.filter(bed_package=None)
        elif type == "IPD":
            queryset = queryset.exclude(bed_package=None)
        if start and end:
            queryset = queryset.filter(from_date__lte=start, to_date__gte=end) \
                       | queryset.filter(from_date__gte=start, to_date__lte=end) \
                       | queryset.filter(from_date__lte=start, to_date__gte=start).filter(from_date__lte=end,
                                                                                          to_date__lte=end) \
                       | queryset.filter(from_date__gte=start, to_date__gte=start).filter(from_date__lte=end,
                                                                                          to_date__gte=end)
        queryset = queryset.distinct()
        if report_type == "DAILY":
            queryset = queryset.filter(payment_status="SUCCESSFUL").values('from_date') \
                .annotate(year=Year('from_date'), month=Month('from_date'), day=Day('from_date')) \
                .values('year', 'month', 'day').annotate(total=Sum('total_price'), count=Count('id')) \
                .order_by('-year', '-month', '-day')
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
                        "Total Booking": item['count'],
                        "Amount(INR)": item['total']
                    })
                subject = "Daily Booking Count Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Booking_count_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        elif report_type == "MONTHLY":
            queryset = queryset.filter(payment_status="SUCCESSFUL").values('from_date') \
                .annotate(year=Year('from_date'), month=Month('from_date')).values('year', 'month') \
                .annotate(total=Sum('total_price'), count=Count('id')).order_by('-year', '-month')
            for res in queryset:
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime(int(res['year']), int(res['month']), 1).date()
            if mail_to:
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Month": item['date'].strftime("%B %Y") if item['date'] else "--",
                        "Total Booking": item['count'],
                        "Amount(INR)": item['total']
                    })
                subject = "Monthly Booking Count Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Booking_count_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        elif report_type == "MEDICINE_COUNT":
            queryset = queryset.filter(payment_status="SUCCESSFUL").exclude(medicines__medicine__name=None).values(
                'medicines__medicine__name').annotate(count=Count('medicines__medicine__name'),
                                                      medicine=F('medicines__medicine__name')).values(
                'count', 'medicine').order_by('-count')
            if mail_to:
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Medicine Name": item['medicine'],
                        "Total Medicine": item['count']
                    })
                subject = "Medicine Usage Count Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Medicine_usage_count_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        elif report_type == "BED_PACKAGE_COUNT":
            queryset = queryset.filter(payment_status="SUCCESSFUL").exclude(bed_package__name=None) \
                .values('bed_package__name').annotate(count=Count('bed_package__name'),
                                                      bed_package=F('bed_package__name')).values(
                'count', 'bed_package').order_by('-count')
            if mail_to:
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Bed Package Name": item['bed_package'],
                        "Total Bed Package": item['count']
                    })
                subject = "Bed Booking Package Count Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Bed_Booking_package_count_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        else:
            if mail_to:
                for index, item in enumerate(queryset):
                    medicines = ""
                    for i, medicine in enumerate(item.medicines.all()):
                        if i + 1 == len(item.medicines.all()):
                            medicines += medicine.name if medicine.name else "--"
                        else:
                            medicines += medicine.name + "," if medicine.name else "--"
                    ready_data.append({
                        "S. No.": index + 1,
                        "Patient Name": item.patient.user.first_name if item.patient and item.patient.user \
                                                                        and item.patient.user.first_name else "--",
                        "Package Name": item.bed_package.name if item.bed_package and item.bed_package.name else "--",
                        "Medicine Package": medicines,
                        "Booking From": item.from_date.strftime("%d/%m/%Y") if item.from_date else "--",
                        "Booking To": item.to_date.strftime("%d/%m/%Y") if item.to_date else "--",
                        "Booking Type": item.seat_type if item.seat_type else "--",
                        "Seat Number": item.seat_no if item.seat_no else "--",
                        "Total Price": item.total_price,
                        "Payment Status": item.payment_status
                    })
                subject = "Bed Booking Report for " + practice_name + " from " + start + " to " + end
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Bed_Booking_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
                if "error" in queryset and queryset["error"]:
                    return response.BadRequest(queryset)
                else:
                    return response.Ok(queryset)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(ReservationsDataSerializer(page, many=True).data)
            return response.Ok(ReservationsDataSerializer(queryset, many=True).data)

    @action(methods=['POST'], detail=True)
    def seat_booking(self, request, *args, **kwargs):
        from ..billing.serializers import PatientInvoicesDataSerializer, PatientPaymentSerializer
        practice = self.get_object()
        data = request.data.copy()
        start = data["from_date"]
        end = data["to_date"]
        seat_type = data["seat_type"]
        paid = data["paid"]
        bed_package = data["bed_package"]
        details = data.pop("details", None)
        package = None
        if details:
            data["details"] = json.dumps(details)
        if bed_package:
            package = BedBookingPackage.objects.get(id=bed_package)
        if package and bed_package and seat_type == "NORMAL":
            data["bed_package_price"] = package.normal_price
            data["bed_package_tax"] = package.normal_tax_value
        elif package and bed_package and seat_type == "TATKAL":
            data["bed_package_price"] = package.tatkal_price
            data["bed_package_tax"] = package.tatkal_tax_value
        is_staff = False
        data["date"] = datetime.now().date()
        result = seat_availability(practice, start, end, bed_package)
        if bed_package and "detail" in result:
            return response.BadRequest(result)
        elif not bed_package or result[seat_type]["available"]:
            data["seat_no"] = result[seat_type]["seat_no"] if bed_package else None
            data["practice"] = practice.pk
            data["user"] = request.user.pk if not request.user.is_anonymous else None
            staff = PracticeStaff.objects.filter(user=request.user).first() if not request.user.is_anonymous else None
            if staff:
                is_staff = True
                data["payment_type"] = "Cash"
                if "pay_value" in data and data["pay_value"] > 0:
                    data["payment_status"] = "SUCCESSFUL"
                serializer = ReservationsStaffSerializer(data=data, partial=True)
            else:
                serializer = ReservationsSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer = serializer.save()
            if staff:
                inv_data = {
                    "practice": practice.pk,
                    "patient": data["patient"],
                    "staff": staff.pk,
                    "reservation": serializer.id,
                    "taxes": data["total_tax"],
                    "total": data["total_price"],
                    "is_pending": not paid,
                    "date": data["date"],
                    "type": "Bed Booking"
                }
                inv_serializer = PatientInvoicesDataSerializer(data=inv_data, partial=True)
                inv_serializer.is_valid(raise_exception=True)
                inv_serializer = inv_serializer.save()
                if "pay_value" in data and data["pay_value"] > 0:
                    pay_data = {
                        "practice": practice.pk,
                        "patient": data["patient"],
                        "staff": staff.pk,
                        "invoices": [{
                            "invoice": inv_serializer.id,
                            "pay_amount": data["pay_value"],
                            "type": "Bed Booking"
                        }],
                        "date": data["date"],
                        "payment_mode": data["payment_mode"],
                        "type": "Bed Booking"
                    }
                    pay_serializer = PatientPaymentSerializer(data=pay_data, partial=True)
                    pay_serializer.is_valid(raise_exception=True)
                    pay_serializer.save()
            return response.Ok({"detail": "Booking Successful", "is_staff": is_staff, "id": serializer.id})
        else:
            return response.BadRequest({"detail": "This Seat is not available for booking in requested time period."})

    @action(methods=['POST'], detail=False)
    def accept_payments(self, request, *args, **kwargs):
        from ..billing.serializers import PatientInvoicesDataSerializer, PatientPaymentSerializer
        from ..patients.models import Reservations
        data = request.data.copy()
        reservation_id = data.get("reservation_id", None)
        try:
            reservation = Reservations.objects.get(id=reservation_id)
        except:
            return response.BadRequest({"detail": "Invalid Reservation/Package"})
        payment_id = data["payment_id"]
        if reservation.bed_package:
            result = seat_availability(reservation.practice, reservation.from_date, reservation.to_date,
                                       reservation.bed_package.pk)
            if "detail" in result:
                capture = False
                msg = result["detail"]
            elif result[reservation.seat_type]['available']:
                reservation.seat_no = result[reservation.seat_type]['seat_no']
                capture = True
            else:
                msg = "No Seats available. Your Payment will be refunded within 7 working days."
                capture = False
        else:
            capture = True
        if capture:
            payment_response = payment_capture(payment_id, round(reservation.total_price))
            if payment_response["error"]:
                return response.BadRequest(payment_response)
            else:
                reservation.payment_status = "SUCCESSFUL"
                reservation.payment_id = payment_id
                patient = reservation.patient.pk if reservation.patient else None
                inv_data = {
                    "practice": reservation.practice.pk,
                    "patient": patient,
                    "reservation": reservation_id,
                    "taxes": reservation.total_tax,
                    "total": reservation.total_price,
                    "is_pending": False,
                    "date": reservation.date,
                    "type": "Bed Booking"
                }
                inv_serializer = PatientInvoicesDataSerializer(data=inv_data, partial=True)
                inv_serializer.is_valid(raise_exception=True)
                inv_serializer = inv_serializer.save()
                pay_data = {
                    "practice": reservation.practice.pk,
                    "patient": patient,
                    "invoices": [{
                        "invoice": inv_serializer.id,
                        "pay_amount": reservation.total_price,
                        "type": "Bed Booking"
                    }],
                    "date": reservation.date,
                    "type": "Bed Booking"
                }
                pay_serializer = PatientPaymentSerializer(data=pay_data, partial=True)
                pay_serializer.is_valid(raise_exception=True)
                pay_serializer = pay_serializer.save()
                reservation.save()
                payment_response["invoice"] = inv_serializer.id
                payment_response["payment"] = pay_serializer.id
                return response.Ok(payment_response)
        else:
            return response.BadRequest({"detail": msg})

    @action(methods=['GET', 'POST'], detail=True)
    def other_diseases(self, request, *args, **kwargs):
        practice = self.get_object()
        if request.method == 'GET':
            data = OtherDiseases.objects.filter(is_active=True)
            if practice:
                data = data.filter(practice=practice)
            return response.Ok(OtherDiseasesSerializer(data.order_by('-id'), many=True).data)
        else:
            data = request.data.copy()
            disease_id = data.pop("id", None)
            data["practice"] = practice.pk
            if disease_id:
                disease_obj = OtherDiseases.objects.get(id=disease_id)
                serializer = OtherDiseasesSerializer(instance=disease_obj, data=data, partial=True)
            else:
                serializer = OtherDiseasesSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_response = serializer.save()
            return response.Ok(OtherDiseasesSerializer(instance=update_response).data)

    @action(methods=['POST'], detail=True)
    def all_print_settings(self, request, *args, **kwargs):
        practice_instance = self.get_object()
        data = request.data.copy()
        subtypes = []
        if "type" in data and data["type"] == "EMR":
            subtypes = ['PRESCRIPTION', 'TREATMENT PLAN', 'CASE SHEET', 'MEDICAL LEAVE', 'REPORT MANUAL', 'LAB ORDER',
                        'CLINICAL NOTES']
        elif "type" in data and data["type"] == "BILLING":
            subtypes = ['INVOICE', 'RECEIPTS', 'RETURN', 'BOOKING', 'PROFORMA']
        practice = practice_instance.pk
        for subtype in subtypes:
            data["sub_type"] = subtype
            data["practice"] = practice
            type = data["type"] if "type" in data else None
            try:
                instance = PracticePrintSettings.objects.get(type=type, sub_type=subtype, practice=practice)
            except:
                instance = None
            if instance:
                serializer = PracticePrintSettingsSerializer(instance=instance, data=data, partial=True)
            else:
                serializer = PracticePrintSettingsSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return response.Ok(data) if len(subtypes) > 0 else response.BadRequest({"detail": "Send proper type in data"})


class PracticeStaffViewSet(ModelViewSet):
    serializer_class = PracticeStaffSerializer
    queryset = PracticeStaff.objects.all()
    permission_classes = (PracticeStaffPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        print('get quer')
        is_manager = self.request.query_params.get("is_manager", None)
        queryset = super(PracticeStaffViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        if is_manager:
            is_manager = True if is_manager == "true" else False
            queryset = queryset.filter(is_manager=is_manager)
        return queryset

    def update(self, request, *args, **kwargs):
        data = request.data
        queryset = super(PracticeStaffViewSet, self).get_queryset()
        queryset = queryset.filter(pk=kwargs.get('pk'))
        roles = data.pop('role') if 'role' in data else None
        employees = data.pop('employees') if 'employees' in data else None
        advisors = data.pop('advisors') if 'advisors' in data else None
        user_obj = None
        if 'user' in data:
            user = data.pop('user')
            user_id = queryset.filter(pk=kwargs.get('pk')).values('user').first()['user']
            mobile = user.get('mobile')
            if User.objects.filter(mobile=mobile).exists():
                user_id = User.objects.filter(mobile=mobile).first().pk
            name = user.get('first_name')
            email = user.get('email')
            User.objects.filter(id=user_id).update(first_name=name, email=email, mobile=mobile, is_active=True)
            user_obj = User.objects.filter(id=user_id).first()
        if user_obj:
            queryset.update(**data, user=user_obj)
        else:
            queryset.update(**data)
        staffobj = PracticeStaff.objects.get(id=kwargs.get('pk'))
        if roles:
            staffobj.role.set(roles)
        if employees:
            staffobj.employees.set(employees)
        if advisors:
            staffobj.advisors.set(advisors)
        staffobj.save()
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.get_serializer(instance)
        return response.Ok(serializer.data)

    @action(methods=['GET'], detail=False)
    def roles(self, request, *args, **kwargs):
        return response.Ok(RoleSerializer(Role.objects.all(), many=True).data)

    @action(methods=['GET'], detail=True)
    def employees(self, request, *args, **kwargs):
        emp_obj = self.get_object()
        return response.Ok(PracticeStaffBasicSerializer(emp_obj.employees.all(), many=True).data)

    @action(methods=['GET'], detail=True)
    def advisors(self, request, *args, **kwargs):
        emp_obj = self.get_object()
        return response.Ok(PatientsBasicDataSerializer(emp_obj.advisors.all(), many=True).data)

    @action(methods=['GET', 'POST'], detail=True)
    def practice_list(self, request, *args, **kwargs):
        staff = self.get_object().pk
        print('staf',staff)
        if request.method == "GET":
            print('ssssssssssss')
            data = PracticeStaffRelation.objects.filter(staff=staff, is_active=True)
            return response.Ok(PracticeStaffRelationDataSerializer(data, many=True).data)
        else:
            data = request.data.copy()
            data["staff"] = staff
            count = PracticeStaffRelation.objects.filter(staff=staff, practice=data["practice"]).count()
            if count > 0:
                instance = PracticeStaffRelation.objects.get(staff=staff, practice=data["practice"])
                serializer = PracticeStaffRelationSerializer(instance=instance, data=data, partial=True)
            else:
                serializer = PracticeStaffRelationSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_obj = serializer.save()
            return response.Ok(PracticeStaffRelationSerializer(update_obj).data)

    @action(methods=['GET', 'POST'], detail=False)
    def permission_group(self, request, *args, **kwargs):
        if request.method == "GET":
            is_global = request.query_params.get('is_global', None)
            group_id = request.query_params.get('id', None)
            permission_data = PermissionGroup.objects.filter(is_active=True)
            if is_global is not None:
                permission_data = permission_data.filter(is_global=is_global)
            if group_id:
                permission_data = permission_data.filter(id=group_id)
            return response.Ok(PermissionGroupSerializer(permission_data, many=True).data)
        else:
            data = request.data
            group_id = data.get('id', None)
            if group_id:
                instance = PermissionGroup.objects.get(id=group_id, is_active=True)
                serializer = PermissionGroupSerializer(instance=instance, data=data, partial=True)
            else:
                serializer = PermissionGroupSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_obj = serializer.save()
            return response.Ok(PermissionGroupSerializer(update_obj).data)

    @action(methods=['POST'], detail=False)
    def assign_group(self, request, *args, **kwargs):
        data = request.data
        group_id = data.get('group', None)
        practice_id = data.get('practice', None)
        staff_id = data.get('staff', None)
        print('group_id:',group_id,practice_id,staff_id)
        if group_id and practice_id and staff_id:
            user_permission = PracticeUserPermissions.objects.filter(practice=practice_id, staff=staff_id,
                                                                     is_active=True).order_by('-id').all()
            instance = PermissionGroup.objects.filter(id=group_id, is_active=True).first()
            serialized_permission = PermissionGroupSerializer(instance).data
            if instance and serialized_permission:
                serializer_data = []
                for permission in serialized_permission['permissions']:
                    if not user_permission.filter(codename=permission['codename']):
                        data = {"practice": practice_id, "staff": staff_id, "codename": permission['codename']}
                        serializer = PracticeUserPermissionsSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer_data.append(serializer)
                for data in serializer_data:
                    data.save()
                return response.Ok({"detail": 'Group Assinged Successfully.'})
            return response.NoContent({"detail": 'Permission Group do not exist.'})
        return response.NoContent({"detail": 'One or more field is empty.'})


class VendorViewSet(ModelViewSet):
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    permission_classes = (VendorPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(VendorViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


class ExpensesViewSet(ModelViewSet):
    serializer_class = ExpensesSerializer
    queryset = Expenses.objects.all()
    permission_classes = (ExpensesPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ExpensesViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        practice = self.request.query_params.get('practice', None)
        mail_to = self.request.query_params.get('mail_to', None)
        ready_data = []
        practice_name = CONST_GLOBAL_PRACTICE
        if start:
            start_date = timezone.get_day_start(timezone.from_str(start))
            queryset = queryset.filter(expense_date__gte=start_date)
        if end:
            end_date = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(expense_date__lte=end_date)
        if practice:
            queryset = queryset.filter(practice=practice)
            instance = Practice.objects.filter(id=practice).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        result = queryset.order_by('-expense_date')
        if mail_to:
            for index, item in enumerate(result):
                ready_data.append({
                    "S. No.": index + 1,
                    "Date": item.expense_date.strftime("%d/%m/%Y") if item.expense_date else "--",
                    "Expense Type": item.expense_type.name if item.expense_type and item.expense_type.name else "--",
                    "Expense Amount": item.amount if item.amount else 0,
                    "Mode of Payment": item.payment_mode.mode if item.payment_mode and item.payment_mode.mode else "--",
                    "Vendor": item.vendor.name if item.vendor and item.vendor.name else "--",
                    "Notes": item.remark if item.remark else "--"
                })
            subject = "Expense Report from " + start_date.strftime(
                "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
            body = "As Requested on ERP System, Please find the Expense Report in the attachment." \
                   + " <br><br> Thanks & Regards,<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Expense_" + start + "_" + end, mail_to, subject, body)

            return response.Ok(result)
        return result

    def list(self, request):
        queryset = Expenses.objects.all()
        queryset = queryset.filter(is_active=True)
        practice = self.request.query_params.get('practice', None)
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        payment_mode = self.request.query_params.get('payment_mode', None)
        expense_type = self.request.query_params.get('expense_type', None)
        if start:
            start = timezone.get_day_start(timezone.from_str(start))
            queryset = queryset.filter(expense_date__gte=start)
        if end:
            end = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(expense_date__lte=end)
        if payment_mode:
            mode_list = payment_mode.split(",")
            queryset = queryset.filter(payment_mode__in=mode_list)
        if expense_type:
            type_list = expense_type.split(",")
            queryset = queryset.filter(expense_type__in=type_list)
        if practice:
            queryset = queryset.filter(practice=practice)
        serializer = ExpensesDataSerializer(queryset.order_by('expense_date'), many=True)
        return response.Ok(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Expenses.objects.all()
        expense_obj = get_object_or_404(queryset, pk=pk)
        serializer = ExpensesDataSerializer(expense_obj)
        return response.Ok(serializer.data)

    @action(methods=['GET'], detail=False)
    def report(self, request, *args, **kwargs):
        queryset = Expenses.objects.all()
        queryset = queryset.filter(is_active=True)
        practice = request.query_params.get('practice', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        payment_mode = request.query_params.get('payment_mode', None)
        expense_type = request.query_params.get('expense_type', None)
        report_type = request.query_params.get('type', None)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if start and end:
            start_date = timezone.get_day_start(timezone.from_str(start))
            end_date = timezone.get_day_end(timezone.from_str(end))
            queryset = queryset.filter(expense_date__range=[start_date, end_date])
        if payment_mode:
            mode_list = payment_mode.split(",")
            queryset = queryset.filter(payment_mode__in=mode_list)
        if expense_type:
            type_list = expense_type.split(",")
            queryset = queryset.filter(expense_type__in=type_list)
        if practice:
            queryset = queryset.filter(practice=practice)
            instance = Practice.objects.filter(id=practice).first()
            practice_name = instance.name if instance else CONST_GLOBAL_PRACTICE
        if report_type == "DAILY":
            queryset = queryset.values('expense_date').annotate(year=Year('expense_date'), month=Month('expense_date'),
                                                                day=Day('expense_date')).values('year', 'month',
                                                                                                'day').annotate(
                total=Sum('amount')).order_by('-year', '-month', '-day')
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
                        "Total Expenses (INR)": item['total']
                    })
                subject = "Daily Expense Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Daily_Expense_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        elif report_type == "MONTHLY":
            queryset = queryset.values('expense_date').annotate(year=Year('expense_date'),
                                                                month=Month('expense_date')).values('year',
                                                                                                    'month').annotate(
                total=Sum('amount')).order_by('-year', '-month')
            for res in queryset:
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime(int(res['year']), int(res['month']), 1).date()

            if mail_to:
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Month": item['date'].strftime("%B %Y") if item['date'] else "--",
                        "Total Expenses (INR)": item['total']
                    })
                subject = "Monthly Expense Report for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Monthly_Expense_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
                return response.Ok(queryset)
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        elif report_type == "EXPENSE_TYPE":
            queryset = queryset.values('expense_type__name').annotate(total=Sum('amount'),
                                                                      expense=F('expense_type__name')).values('total',
                                                                                                              'expense') \
                .order_by('-total', 'expense')

            if mail_to:
                for index, item in enumerate(queryset):
                    ready_data.append({
                        "S. No.": index + 1,
                        "Expense Name": item['expense'],
                        "Total Expenses (INR)": item['total']
                    })
                subject = "Expenses Type for " + practice_name + " from " + start_date.strftime(
                    "%d/%m/%Y") + " to " + end_date.strftime("%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Expense_For_Each_Type_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}
            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)

            return response.Ok(queryset)
        else:
            return response.BadRequest({"detail": "Invalid Type Sent"})


class ActivityLogViewSet(ModelViewSet):
    serializer_class = ActivityLogSerializer
    queryset = ActivityLog.objects.all()
    permission_classes = (ActivityLogPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        start = self.request.query_params.get("start", None)
        end = self.request.query_params.get("end", None)
        category = self.request.query_params.get("category", None)
        sub_category = self.request.query_params.get("sub_category", None)
        patient = self.request.query_params.get("patient", None)
        practice = self.request.query_params.get("practice", None)
        staff = self.request.query_params.get("staff", None)
        user = self.request.query_params.get("user", None)
        activity = self.request.query_params.get("activity", None)
        queryset = super(ActivityLogViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if category:
            queryset = queryset.filter(component=category)
        if sub_category:
            queryset = queryset.filter(sub_component=sub_category)
        if patient:
            queryset = queryset.filter(patient=patient)
        if practice:
            queryset = queryset.filter(practice=practice)
        if staff:
            queryset = queryset.filter(staff=staff)
        if user:
            queryset = queryset.filter(user=user)
        if activity:
            queryset = queryset.filter(activity=activity)
        return queryset

    @action(methods=['GET'], detail=False)
    def category(self, request, *args, **kwargs):
        output = []
        for item in CONST_LOG_GENERATOR:
            if item["Category"] not in output:
                output.append(item["Category"])
        return response.Ok(output)

    @action(methods=['GET'], detail=False)
    def subcategory(self, request, *args, **kwargs):
        category = request.query_params.get("category", None)
        if category:
            output = []
            for item in CONST_LOG_GENERATOR:
                if item["Category"] == category:
                    output.append(item["SubCategory"])
            return response.Ok(output)
        else:
            return response.BadRequest({"detail": "No Category Selected"})


class DrugTypeViewSet(ModelViewSet):
    serializer_class = DrugTypeSerializer
    queryset = DrugType.objects.all()
    permission_classes = (DrugTypePermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(DrugTypeViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


class DrugUnitViewSet(ModelViewSet):
    serializer_class = DrugUnitSerializer
    queryset = DrugUnit.objects.all()
    permission_classes = (DrugUnitPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(DrugUnitViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


class PracticeUserPermissionsViewSet(ModelViewSet):
    serializer_class = PracticeUserPermissionsSerializer
    queryset = PracticeUserPermissions.objects.all()
    permission_classes = (PracticeUserPermissionsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(PracticeUserPermissionsViewSet, self).get_queryset()
        practice = self.request.query_params.get('practice')
        staff = self.request.query_params.get('staff')
        queryset = queryset.filter(is_active=True)
        if practice:
            queryset = queryset.filter(practice__id=practice) | queryset.filter(practice=None)
        if staff:
            queryset = queryset.filter(staff__id=staff)
        return queryset

    @action(methods=['POST'], detail=False)
    def bulk(self, request, *args, **kwargs):
        data = request.data.copy()
        permissions = data.pop("permissions", [])
        save_data = []
        for permission in permissions:
            permission_id = permission.pop("id", None)
            if permission_id:
                perm_obj = PracticeUserPermissions.objects.get(id=permission_id)
                serializer = PracticeUserPermissionsSerializer(data=permission, instance=perm_obj, partial=True)
            else:
                serializer = PracticeUserPermissionsSerializer(data=permission, partial=True)
            serializer.is_valid(raise_exception=True)
            save_data.append(serializer)
        for serializer in save_data:
            serializer.save()
        return response.Ok({"detail": "User Permissions Updated Successfully"})


class PushNotificationViewSet(ModelViewSet):
    serializer_class = PushNotificationSaveSerializer
    queryset = PushNotifications.objects.all()
    permission_classes = (PracticeUserPermissionsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        self.serializer_class = PushNotificationSerializer
        queryset = super(PushNotificationViewSet, self).get_queryset()
        user_id = self.request.query_params.get('user', None)
        device = self.request.query_params.get('device', None)
        application = self.request.query_params.get('application', None)
        queryset = queryset.filter(is_active=True)
        if user_id:
            queryset = queryset.filter(user=user_id)
        if device:
            queryset = queryset.filter(device=device) | queryset.filter(device=None)
        if application:
            queryset = queryset.filter(application=application) | queryset.filter(application=None)
        return queryset.order_by('-id')
    
class NoticeBoardViewSet(ModelViewSet):
    serializer_class = NoticeBoardSerializer
    queryset = NoticeBoard.objects.all()
    permission_classes = (PracticeUserPermissionsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super(NoticeBoardViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
