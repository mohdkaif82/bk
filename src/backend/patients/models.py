import uuid

from ..accounts.models import User
# Create your models here.
from ..base.models import TimeStampedModel
from ..base.validators.form_validations import file_extension_validator
from ..inventory.models import InventoryItem, StockEntryItem
from ..mlm.models import AgentRole, ProductMargin
from ..muster_roll.models import HrSettings
from ..practice.models import Practice, ProcedureCatalog, Taxes, PaymentModes, \
    DrugType, DrugUnit, PracticeOffers, PracticeStaff, LabTestCatalog, Filetags, Membership, BedBookingPackage, \
    MedicineBookingPackage, OtherDiseases, Registration
from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Source(TimeStampedModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class State(models.Model):
    name = models.CharField(max_length=1024, null=True, blank=True)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class City(models.Model):
    name = models.CharField(max_length=1024, null=True, blank=True)
    state = models.ForeignKey(State, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class PatientMedicalHistory(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PatientGroups(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PersonalDoctorsPractice(models.Model):
    practice = models.ForeignKey(Practice, null=True, blank=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

class Service(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='services/')
    is_active = models.BooleanField(default=True)

class Patients(TimeStampedModel):
    user = models.OneToOneField(User, blank=True, null=True, related_name="patients_user", on_delete=models.PROTECT)
    approved_by = models.ForeignKey(User, blank=True, null=True, related_name="advisor_user",
                                    on_delete=models.PROTECT)
    aadhar_id = models.CharField(max_length=25, null=True, blank=True)
    pan_card_id = models.CharField(max_length=25, null=True, blank=True)
    gender = models.CharField(max_length=256, null=True, blank=True)
    custom_id = models.CharField(max_length=256, null=True, blank=True)
    dob = models.DateField(blank=True, null=True)
    is_age = models.BooleanField(default=False)
    self_register = models.BooleanField(default=False)
    on_dialysis = models.BooleanField(default=False)
    anniversary = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=256, null=True, blank=True)
    source = models.ForeignKey(Source, null=True, blank=True, on_delete=models.PROTECT)
    family_relation1 = models.CharField(max_length=1024, null=True, blank=True)
    family_relation2 = models.CharField(max_length=1024, null=True, blank=True)
    attendee1 = models.CharField(max_length=1024, null=True, blank=True)
    attendee1_mobile_no = models.CharField(max_length=1024, null=True, blank=True)
    attendee2 = models.CharField(max_length=1024, null=True, blank=True)
    attendee2_mobile_no = models.CharField(max_length=1024, null=True, blank=True)
    secondary_mobile_no = models.CharField(max_length=1024, blank=True, null=True)
    landline_no = models.CharField(max_length=1024, blank=True, null=True)
    language = models.CharField(max_length=512, blank=True, null=True)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT,
                                 related_name="advisor_practice")
    religion = models.ForeignKey(HrSettings, blank=True, related_name="religion", null=True,
                                 on_delete=models.PROTECT)
    address = models.TextField(blank=True, null=True)
    locality = models.TextField(blank=True, null=True)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT)
    state = models.ForeignKey(State, blank=True, null=True, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.PROTECT)
    pd_doctor = models.ForeignKey(PracticeStaff, null=True, blank=True, on_delete=models.PROTECT)
    pd_doctor_added = models.DateTimeField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    image = models.CharField(max_length=1024, blank=True, null=True)
    medical_history = models.ManyToManyField(PatientMedicalHistory, blank=True)
    patient_group = models.ManyToManyField(PatientGroups, blank=True)
    practices = models.ManyToManyField(PersonalDoctorsPractice, blank=True)
    sms_enable = models.BooleanField(default=True)
    email_enable = models.BooleanField(default=True)
    file_enable = models.BooleanField(default=True)
    file_count = models.PositiveSmallIntegerField(null=True, blank=True)
    birthday_sms_email = models.BooleanField(default=True)
    follow_up_sms_email = models.BooleanField(default=True)
    medicine_from = models.DateField(null=True, blank=True)
    medicine_till = models.DateField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_staff = models.ForeignKey(PracticeStaff, null=True, blank=True, on_delete=models.PROTECT,
                                        related_name="followup_staff")
    follow_up_date_email = models.DateField(null=True, blank=True)
    is_dead = models.BooleanField(default=False)
    dead_by = models.ForeignKey(PracticeStaff, null=True, blank=True, on_delete=models.PROTECT, related_name="dead_by")
    is_active = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    advisor_joined = models.DateTimeField(null=True, blank=True)
    role = models.ForeignKey(AgentRole, blank=True, null=True, on_delete=models.PROTECT)
    aadhar_upload = models.CharField(max_length=1024, null=True, blank=True)
    pan_upload = models.CharField(max_length=1024, null=True, blank=True)


class ColdCalling(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    mobile = models.CharField(max_length=100, blank=True, null=True)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT)
    state = models.ForeignKey(State, blank=True, null=True, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.PROTECT)
    pincode = models.IntegerField(null=True, blank=True)
    medical_history = models.ManyToManyField(PatientMedicalHistory, blank=True)
    remarks = models.CharField(max_length=1024, blank=True, null=True)
    status = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_advisor = models.BooleanField(default=False)
    created_staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    created_advisor = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)


class PatientVitalSigns(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateTimeField(null=True, blank=True)
    pulse = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    temperature_part = models.CharField(max_length=524, blank=True, null=True)
    blood_pressure_up = models.CharField(max_length=50, null=True, blank=True)
    blood_pressure_down = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=524, blank=True, null=True)
    weight = models.FloatField(null=True, blank=True)
    creatinine = models.FloatField(null=True, blank=True)
    urea = models.FloatField(null=True, blank=True)
    haemoglobin = models.FloatField(null=True, blank=True)
    uric_acid = models.FloatField(null=True, blank=True)
    resp_rate = models.FloatField(null=True, blank=True)
    remarks = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class PatientClinicNotes(TimeStampedModel):
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    chief_complaints = models.CharField(max_length=2028, blank=True, null=True)
    investigations = models.CharField(max_length=2028, blank=True, null=True)
    diagnosis = models.CharField(max_length=2028, blank=True, null=True)
    notes = models.CharField(max_length=2028, blank=True, null=True)
    observations = models.CharField(max_length=2028, blank=True, null=True)
    medication = models.CharField(max_length=2028, blank=True, null=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(null=True, blank=True)
    follow_up = models.BooleanField(default=True)


class PatientTreatmentPlans(TimeStampedModel):
    procedure = models.ForeignKey(ProcedureCatalog, blank=True, null=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    default_notes = models.TextField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    discount = models.FloatField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)


class PatientProcedure(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    treatment_plans = models.ManyToManyField(PatientTreatmentPlans, blank=True)


class PatientAllopathicMedicines(TimeStampedModel):
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, null=True, blank=True)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    dosage_details = models.CharField(max_length=1024, null=True, blank=True)
    formula = models.CharField(max_length=1024, blank=True, null=True)
    remarks = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PatientFile(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    file_tags = models.ManyToManyField(Filetags, blank=True)
    file_type = models.CharField(max_length=524, blank=True, null=True)
    upload_by = models.CharField(max_length=524, blank=True, null=True, default="STAFF")
    is_mailed = models.BooleanField(default=False)


class PatientInventory(TimeStampedModel):
    inventory = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    quantity = models.PositiveIntegerField(null=True, blank=True, default=0)
    unit = models.CharField(max_length=1024, blank=True, null=True)
    dosage = models.CharField(max_length=1024, blank=True, null=True)
    frequency = models.CharField(max_length=1024, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, default=0)
    duration_type = models.CharField(max_length=10, blank=True, null=True)
    before_food = models.BooleanField(default=False)
    after_food = models.BooleanField(default=False)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_billed = models.BooleanField(default=False)


class PatientAdvice(models.Model):
    details = models.CharField(max_length=1024, null=True, blank=True)


class PatientPrescriptions(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    drugs = models.ManyToManyField(PatientInventory, blank=True)
    labs = models.ManyToManyField(LabTestCatalog, blank=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(null=True, blank=True)
    follow_up = models.BooleanField(default=False)
    days = models.IntegerField(null=True, blank=True)
    input_time = models.IntegerField(null=True, blank=True)
    time_type = models.CharField(max_length=10, null=True, blank=True)
    advice = models.BooleanField(default=False)
    advice_data = models.ManyToManyField(PatientAdvice, blank=True)
    doctor_notes = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ProcedureCatalogInvoice(TimeStampedModel):
    procedure = models.ForeignKey(ProcedureCatalog, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, null=True, blank=True)
    unit_cost = models.FloatField(null=True, blank=True)
    discount = models.FloatField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    offers = models.ForeignKey(PracticeOffers, blank=True, null=True, on_delete=models.PROTECT)
    unit = models.PositiveSmallIntegerField(blank=True, null=True)
    default_notes = models.TextField(null=True, blank=True)
    taxes = models.ManyToManyField(Taxes, blank=True)
    is_active = models.BooleanField(default=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True)
    total = models.FloatField(null=True, blank=True)
    tax_value = models.FloatField(null=True, blank=True)
    discount_value = models.FloatField(null=True, blank=True)


class InventoryCatalogInvoice(TimeStampedModel):
    inventory = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    drug_unit = models.ForeignKey(DrugUnit, blank=True, null=True, on_delete=models.PROTECT)
    drug_type = models.ForeignKey(DrugType, blank=True, null=True, on_delete=models.PROTECT)
    strength = models.IntegerField(blank=True, null=True)
    dosage = models.CharField(max_length=1024, blank=True, null=True)
    frequency = models.CharField(max_length=1024, blank=True, null=True)
    unit = models.PositiveSmallIntegerField(blank=True, null=True)
    unit_cost = models.FloatField(null=True, blank=True)
    discount = models.FloatField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    offers = models.ForeignKey(PracticeOffers, blank=True, null=True, on_delete=models.PROTECT)
    taxes = models.ManyToManyField(Taxes, blank=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    total = models.FloatField(null=True, blank=True)
    tax_value = models.FloatField(null=True, blank=True)
    discount_value = models.FloatField(null=True, blank=True)
    batch_number = models.CharField(max_length=1024, blank=True, null=True)
    stock = models.ForeignKey(StockEntryItem, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True)


PaymentType = (
    ('Cash', 'CASH'),
    ('Online', 'ONLINE')
)


class MedicineBooking(TimeStampedModel):
    medicine = models.ForeignKey(MedicineBookingPackage, blank=True, null=True, on_delete=models.PROTECT)
    taxes = models.ManyToManyField(Taxes, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    unit_cost = models.FloatField(null=True, blank=True)
    discount_value = models.FloatField(null=True, blank=True)
    total_price = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Reservations(TimeStampedModel):
    name = models.CharField(max_length=512, null=True, blank=True)
    mobile = models.CharField(max_length=512, null=True, blank=True)
    email = models.CharField(max_length=512, null=True, blank=True)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    bed_package = models.ForeignKey(BedBookingPackage, blank=True, null=True, on_delete=models.PROTECT)
    medicines = models.ManyToManyField(MedicineBooking, blank=True)
    other_diseases = models.ManyToManyField(OtherDiseases, blank=True)
    bed_package_tax = models.FloatField(null=True, blank=True)
    bed_package_price = models.FloatField(null=True, blank=True)
    taxes = models.ManyToManyField(Taxes, blank=True)
    total_tax = models.FloatField(null=True, blank=True)
    total_price = models.FloatField(null=True, blank=True)
    payment_id = models.CharField(max_length=512, null=True, blank=True)
    payment_status = models.CharField(max_length=512, null=True, blank=True, default="PENDING")
    seat_type = models.CharField(max_length=512, null=True, blank=True)
    seat_no = models.CharField(max_length=512, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    patient = models.ForeignKey(Patients, null=True, blank=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="reservation_user")
    payment_type = models.CharField(max_length=512, null=True, blank=True, choices=PaymentType)
    payment_mode = models.ForeignKey(PaymentModes, blank=True, null=True, on_delete=models.PROTECT)
    delivery_address = models.CharField(max_length=4000, null=True, blank=True)
    delivery_contact = models.CharField(max_length=100, null=True, blank=True)
    dialysis = models.BooleanField(default=False)
    creatinine = models.CharField(max_length=512, null=True, blank=True)
    urea_level = models.CharField(max_length=512, null=True, blank=True)
    report_upload = models.CharField(max_length=512, null=True, blank=True)
    remark = models.CharField(max_length=1024, null=True, blank=True)
    rest_diseases = models.CharField(max_length=1024, null=True, blank=True)
    details = models.CharField(max_length=4000, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    from_website = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class PatientInvoices(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    procedure = models.ManyToManyField(ProcedureCatalogInvoice, blank=True)
    inventory = models.ManyToManyField(InventoryCatalogInvoice, blank=True)
    prescription = models.ManyToManyField(PatientPrescriptions, blank=True)
    reservation = models.ForeignKey(Reservations, blank=True, null=True, on_delete=models.PROTECT)
    cost = models.FloatField(null=True, blank=True, default=0)
    discount = models.FloatField(null=True, blank=True, default=0)
    taxes = models.FloatField(null=True, blank=True, default=0)
    total = models.FloatField(null=True, blank=True, default=0)
    is_pending = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)
    invoice_id = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True, default="Invoice")
    notes = models.CharField(max_length=2000, blank=True, null=True)
    promo_code = models.CharField(max_length=512, null=True, blank=True)
    courier_charge = models.FloatField(null=True, blank=True)
    courier_name = models.CharField(max_length=512, null=True, blank=True)
    tracking_number = models.CharField(max_length=512, null=True, blank=True)
    tracking_bill = models.CharField(max_length=512, null=True, blank=True)
    delivery_address = models.CharField(max_length=4000, null=True, blank=True)
    delivery_contact = models.CharField(max_length=100, null=True, blank=True)
    cancel_note = models.CharField(max_length=1000, null=True, blank=True)


class InvoiceDetails(TimeStampedModel):
    invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    pay_amount = models.FloatField(null=True, blank=True)
    pay_amount_advance = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=200, blank=True, null=True, default="Invoice")


class ProcedureCatalogReturn(TimeStampedModel):
    procedure = models.ForeignKey(ProcedureCatalog, blank=True, null=True, on_delete=models.PROTECT)
    procedure_inv = models.ForeignKey(ProcedureCatalogInvoice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, null=True, blank=True)
    unit_cost = models.FloatField(null=True, blank=True)
    discount = models.FloatField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    offers = models.ForeignKey(PracticeOffers, blank=True, null=True, on_delete=models.PROTECT)
    unit = models.PositiveSmallIntegerField(blank=True, null=True)
    default_notes = models.TextField(null=True, blank=True)
    taxes = models.ManyToManyField(Taxes, blank=True)
    is_active = models.BooleanField(default=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    total = models.FloatField(null=True, blank=True)
    tax_value = models.FloatField(null=True, blank=True)
    discount_value = models.FloatField(null=True, blank=True)


class InventoryCatalogReturn(TimeStampedModel):
    inventory = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    inventory_inv = models.ForeignKey(InventoryCatalogInvoice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    drug_unit = models.ForeignKey(DrugUnit, blank=True, null=True, on_delete=models.PROTECT)
    drug_type = models.ForeignKey(DrugType, blank=True, null=True, on_delete=models.PROTECT)
    strength = models.IntegerField(blank=True, null=True)
    dosage = models.CharField(max_length=1024, blank=True, null=True)
    frequency = models.CharField(max_length=1024, blank=True, null=True)
    unit = models.PositiveSmallIntegerField(blank=True, null=True)
    unit_cost = models.FloatField(null=True, blank=True)
    discount = models.FloatField(null=True, blank=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    offers = models.ForeignKey(PracticeOffers, blank=True, null=True, on_delete=models.PROTECT)
    taxes = models.ManyToManyField(Taxes, blank=True)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    total = models.FloatField(null=True, blank=True)
    tax_value = models.FloatField(null=True, blank=True)
    discount_value = models.FloatField(null=True, blank=True)
    batch_number = models.CharField(max_length=1024, blank=True, null=True)
    stock = models.ForeignKey(StockEntryItem, blank=True, null=True, on_delete=models.PROTECT)


class ReturnPayment(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    return_mode = models.ForeignKey(PaymentModes, blank=True, null=True, on_delete=models.PROTECT)
    invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    procedure = models.ManyToManyField(ProcedureCatalogReturn, blank=True)
    inventory = models.ManyToManyField(InventoryCatalogReturn, blank=True)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    bank = models.CharField(max_length=200, blank=True, null=True)
    number = models.CharField(max_length=20, blank=True, null=True)
    with_tax = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)
    cost = models.FloatField(null=True, blank=True, default=0)
    discount = models.FloatField(null=True, blank=True, default=0)
    taxes = models.FloatField(null=True, blank=True, default=0)
    total = models.FloatField(null=True, blank=True, default=0)
    return_value = models.FloatField(null=True, blank=True, default=0)
    cash_return = models.FloatField(null=True, blank=True, default=0)
    return_id = models.CharField(max_length=200, blank=True, null=True)
    cancel_note = models.CharField(max_length=1000, null=True, blank=True)


class PatientPayment(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentModes, blank=True, null=True, on_delete=models.PROTECT)
    return_pay = models.ForeignKey(ReturnPayment, blank=True, null=True, on_delete=models.PROTECT)
    invoices = models.ManyToManyField(InvoiceDetails, blank=True)
    bank = models.CharField(max_length=200, blank=True, null=True)
    number = models.CharField(max_length=2000, blank=True, null=True)
    advance_value = models.FloatField(null=True, blank=True)
    is_advance = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    date = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True, default="Payment")
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    cancel_note = models.CharField(max_length=1000, null=True, blank=True)


class CalculateMlm(TimeStampedModel):
    invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    mlm_amount = models.FloatField(null=True, blank=True, default=0)
    is_active = models.BooleanField(default=True)


class PatientWallet(TimeStampedModel):
    patient = models.OneToOneField(Patients, unique=True, null=True, on_delete=models.PROTECT)
    refundable_amount = models.FloatField(blank=True, null=True, default=0)
    non_refundable = models.FloatField(blank=True, null=True, default=0)


class PatientWalletLedger(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    payment = models.ForeignKey(PatientPayment, blank=True, null=True, on_delete=models.PROTECT)
    invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    mlm = models.ForeignKey(CalculateMlm, blank=True, null=True, on_delete=models.PROTECT)
    ledger_type = models.CharField(max_length=50, null=True, blank=True, default="Credit")
    amount = models.FloatField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    amount_type = models.CharField(max_length=50, null=True, blank=True, default="Non Refundable")
    comments = models.CharField(max_length=1024, null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    is_mlm = models.BooleanField(default=False)


class PatientMembership(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    medical_membership = models.ForeignKey(Membership, blank=True, null=True, on_delete=models.PROTECT)
    membership_invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    membership_payments = models.ForeignKey(PatientPayment, related_name='payment_member', blank=True, null=True,
                                            on_delete=models.PROTECT)
    membership_benefit = models.ForeignKey(PatientPayment, related_name='benefit_member', blank=True, null=True,
                                           on_delete=models.PROTECT)
    medical_from = models.DateField(null=True, blank=True)
    medical_to = models.DateField(null=True, blank=True)
    membership_code = models.CharField(max_length=1024, null=True, blank=True)
    membership_upload = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class PatientRegistration(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    registration = models.ForeignKey(Registration, blank=True, null=True, on_delete=models.PROTECT)
    registration_invoice = models.ForeignKey(PatientInvoices, blank=True, null=True, on_delete=models.PROTECT)
    registration_payments = models.ForeignKey(PatientPayment, blank=True, null=True, on_delete=models.PROTECT)
    registration_from = models.DateField(null=True, blank=True)
    registration_to = models.DateField(null=True, blank=True)
    registration_upload = models.CharField(max_length=1024, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class GeneratedPdf(TimeStampedModel):
    uuid = models.CharField(default=uuid.uuid4().hex[:8], max_length=40, )
    name = models.CharField(max_length=40, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    report = models.FileField(upload_to="pdf_data/%Y/%m/%d", max_length=80, blank=True, null=True,
                              validators=[file_extension_validator])


class PatientNotes(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class PatientCallNotes(TimeStampedModel):
    from ..meeting.models import Meeting
    empty = models.CharField(max_length=1024, blank=True, null=True)
    remarks = models.CharField(max_length=1024, blank=True, null=True)
    type = models.CharField(max_length=1024, blank=True, null=True, default="Audio")
    response = models.CharField(max_length=1024, blank=True, null=True)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    practice_staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.CharField(max_length=1024, blank=True, null=True)
    staff_id = models.CharField(max_length=1024, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    meeting = models.ForeignKey(Meeting, null=True, blank=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class MedicalCertificate(TimeStampedModel):
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    excused_duty = models.BooleanField(default=False)
    excused_duty_from = models.DateField(blank=True, null=True)
    excused_duty_to = models.DateField(blank=True, null=True)
    excused_duty_from_session = models.CharField(max_length=1024, blank=True, null=True)
    excused_duty_to_session = models.CharField(max_length=1024, blank=True, null=True)
    fit_light_duty = models.BooleanField(default=False)
    fit_light_duty_from = models.DateField(blank=True, null=True)
    fit_light_duty_to = models.DateField(blank=True, null=True)
    proof_attendance = models.BooleanField(default=False)
    proof_attendance_date = models.DateField(blank=True, null=True)
    proof_attendance_from = models.TimeField(blank=True, null=True)
    proof_attendance_to = models.TimeField(blank=True, null=True)
    notes = models.CharField(max_length=1024, blank=True, null=True)
    valid_court = models.BooleanField(default=False)
    invalid_court = models.BooleanField(default=False)
    no_mention = models.BooleanField(default=True)
    date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class RequestOTP(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, blank=True, null=True, related_name="otp_user", on_delete=models.PROTECT)
    otp = models.IntegerField(blank=True, null=True)
    phone_no = models.CharField(max_length=15, null=True)
    cancel_type = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)


class PatientsPromoCode(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    patients = models.ManyToManyField(Patients, blank=True)
    promo_code = models.CharField(max_length=50, null=True, blank=True)
    code_value = models.FloatField(blank=True, null=True)
    code_type = models.CharField(max_length=10, null=True, blank=True, default="%")
    minimum_order = models.FloatField(blank=True, null=True, default=0)
    maximum_discount = models.FloatField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    sms_sent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class AdvisorBank(TimeStampedModel):
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    account_name = models.CharField(max_length=1024, blank=True, null=True)
    account_number = models.CharField(max_length=1024, blank=True, null=True)
    ifsc_code = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=1024, blank=True, null=True)
    bank_branch = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
