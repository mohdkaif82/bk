from django.contrib import admin
from .models import Patients, PatientGroups, PatientMedicalHistory, \
    PatientVitalSigns, PatientClinicNotes, PatientTreatmentPlans, State, City, Country, \
    PatientFile, PatientPrescriptions, PatientInvoices, PatientPayment, \
    PatientMembership, ProcedureCatalogInvoice,PatientWallet,AdvisorBank,PatientCallNotes,MedicalCertificate, \
        PatientNotes,PatientRegistration,Source,PatientProcedure,RequestOTP,PatientAdvice


@admin.register(PatientGroups)
class PatientGroupsAdmin(admin.ModelAdmin):
    model = PatientGroups
    
@admin.register(AdvisorBank)
class AdvisorBankAdmin(admin.ModelAdmin):
    model = AdvisorBank
    

@admin.register(PatientAdvice)
class PatientAdviceAdmin(admin.ModelAdmin):
    model = PatientAdvice
    
@admin.register(RequestOTP)
class RequestOTPAdmin(admin.ModelAdmin):
    model = RequestOTP

@admin.register(PatientProcedure)
class PatientProcedureAdmin(admin.ModelAdmin):
    model = PatientProcedure
    
@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    model = Source
    
@admin.register(PatientRegistration)
class PatientRegistrationAdmin(admin.ModelAdmin):
    model = PatientRegistration
    
@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    model = MedicalCertificate
    
 
@admin.register(PatientNotes)
class PatientNotesAdmin(admin.ModelAdmin):
    model = PatientNotes

    
@admin.register(PatientCallNotes)
class PatientCallNotesAdmin(admin.ModelAdmin):
    model = PatientCallNotes
    
@admin.register(PatientWallet)
class PatientWallet(admin.ModelAdmin):
    model = PatientWallet


@admin.register(PatientMedicalHistory)
class PatientMedicalHistoryAdmin(admin.ModelAdmin):
    model = PatientMedicalHistory


@admin.register(Patients)
class PatientsAdmin(admin.ModelAdmin):
    model = Patients


@admin.register(PatientVitalSigns)
class PatientVitalSignsAdmin(admin.ModelAdmin):
    model = PatientVitalSigns


@admin.register(PatientClinicNotes)
class PatientClinicNotesAdmin(admin.ModelAdmin):
    model = PatientClinicNotes


@admin.register(PatientTreatmentPlans)
class PatientTreatmentPlansAdmin(admin.ModelAdmin):
    model = PatientTreatmentPlans


@admin.register(PatientFile)
class PatientFileAdmin(admin.ModelAdmin):
    model = PatientFile


@admin.register(PatientPrescriptions)
class PatientPrescriptionsAdmin(admin.ModelAdmin):
    model = PatientPrescriptions


@admin.register(PatientInvoices)
class PatientInvoicesAdmin(admin.ModelAdmin):
    model = PatientInvoices


@admin.register(PatientPayment)
class PatientPaymentAdmin(admin.ModelAdmin):
    model = PatientPayment


@admin.register(PatientMembership)
class PatientMemberShipAdmin(admin.ModelAdmin):
    model = PatientMembership


@admin.register(ProcedureCatalogInvoice)
class ProcedureCatalogInvoiceAdmin(admin.ModelAdmin):
    model = ProcedureCatalogInvoice


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    model = State

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    model = City

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    model = Country
    
    
