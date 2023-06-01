from .models import Practice, PracticeCalenderSettings, AppointmentCategory, PracticeStaff, \
    VisitingTime, ProcedureCatalog, Taxes, DrugUnit, PaymentModes, PracticeOffers, PracticeReferer, \
    PracticeComplaints, Observations, Diagnoses, Investigations, Treatmentnotes, Filetags, Communications, LabPanel, \
    LabTestCatalog, DrugCatalog, DrugType, PracticeUserPermissions, PracticePrintSettings,PracticeStaffRelation,\
    PushNotifications,Membership,Registration,EmailCommunications
from django.contrib import admin

from .models import Doctor, Disease

admin.site.register(Doctor)
admin.site.register(Disease)
@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    model = Practice
    list_display = ('id', 'name',)

@admin.register(PracticeStaffRelation)
class PracticeStaffRelation(admin.ModelAdmin):
    model = PracticeStaffRelation
    

@admin.register(EmailCommunications)
class EmailCommunications(admin.ModelAdmin):
    model = EmailCommunications
    
@admin.register(Registration)
class RegistrationRelation(admin.ModelAdmin):
    model = Registration

@admin.register(Membership)
class membershipRelation(admin.ModelAdmin):
    model = Membership
    
@admin.register(PushNotifications)
class PushNotificationsAdmin(admin.ModelAdmin):
    model = PushNotifications

@admin.register(PracticeCalenderSettings)
class PracticeCalenderSettingsAdmin(admin.ModelAdmin):
    model = PracticeCalenderSettings


@admin.register(AppointmentCategory)
class AppointmentCategoryAdmin(admin.ModelAdmin):
    model = AppointmentCategory


@admin.register(PracticeStaff)
class PracticeStaffAdmin(admin.ModelAdmin):
    model = PracticeStaff


@admin.register(PracticePrintSettings)
class PracticePrintSettingsAdmin(admin.ModelAdmin):
    model = PracticePrintSettings


@admin.register(VisitingTime)
class VisitingTimeAdmin(admin.ModelAdmin):
    model = VisitingTime


@admin.register(ProcedureCatalog)
class ProcedureCatalogAdmin(admin.ModelAdmin):
    model = ProcedureCatalog


@admin.register(Communications)
class CommunicationsAdmin(admin.ModelAdmin):
    model = Communications


@admin.register(Taxes)
class TaxesAdmin(admin.ModelAdmin):
    model = Taxes


@admin.register(PaymentModes)
class PaymentModesAdmin(admin.ModelAdmin):
    model = PaymentModes


@admin.register(PracticeOffers)
class PracticeOffersAdmin(admin.ModelAdmin):
    model = PracticeOffers


@admin.register(PracticeReferer)
class PracticeRefererAdmin(admin.ModelAdmin):
    model = PracticeReferer


@admin.register(PracticeComplaints)
class PracticeComplaintsAdmin(admin.ModelAdmin):
    model = PracticeComplaints


@admin.register(LabPanel)
class LabPanelAdmin(admin.ModelAdmin):
    model = LabPanel


@admin.register(LabTestCatalog)
class LabTestCatalogAdmin(admin.ModelAdmin):
    model = LabTestCatalog


@admin.register(DrugCatalog)
class DrugCatalogAdmin(admin.ModelAdmin):
    model = DrugCatalog


@admin.register(DrugType)
class DrugTypeAdmin(admin.ModelAdmin):
    model = DrugType


@admin.register(DrugUnit)
class DrugUnitAdmin(admin.ModelAdmin):
    model = DrugUnit


@admin.register(Observations)
class ObservationsAdmin(admin.ModelAdmin):
    model = Observations


@admin.register(Diagnoses)
class DiagnosesAdmin(admin.ModelAdmin):
    model = Diagnoses


@admin.register(Investigations)
class InvestigationsAdmin(admin.ModelAdmin):
    model = Investigations


@admin.register(Treatmentnotes)
class TreatmentnotesAdmin(admin.ModelAdmin):
    model = Treatmentnotes


@admin.register(Filetags)
class FiletagsAdmin(admin.ModelAdmin):
    model = Filetags


@admin.register(PracticeUserPermissions)
class PracticeUserPermissionsAdmin(admin.ModelAdmin):
    pass
