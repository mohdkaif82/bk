from ..accounts.models import User, Role
from ..base.models import TimeStampedModel
from ..mlm.models import ProductMargin
from django.db import models

ACTIVITY_OPTIONS = (
    ('Added', 'Added'),
    ('Modified', 'Modified'),
    ('Deleted', 'Deleted')
)


class PracticeStaff(TimeStampedModel):
    user = models.ForeignKey(User, blank=True, null=True, related_name="practice_staff_user", on_delete=models.PROTECT)
    role = models.ManyToManyField(Role, blank=True)
    registration_number = models.CharField(max_length=128, null=True, blank=True)
    emp_id = models.CharField(max_length=128, null=True, blank=True)
    calendar_colour = models.CharField(max_length=32, null=True, blank=True)
    confirmation_sms = models.BooleanField(default=False)
    schedule_sms = models.BooleanField(default=False)
    confirmation_email = models.BooleanField(default=False)
    online_appointment_sms = models.BooleanField(default=False)
    activate_login = models.BooleanField(default=False)
    update_timing_online = models.BooleanField(default=True)
    is_manager = models.BooleanField(default=False)
    designation = models.ForeignKey("muster_roll.HrSettings", blank=True, related_name="designation", null=True,
                                    on_delete=models.PROTECT)
    department = models.ForeignKey("muster_roll.HrSettings", blank=True, related_name="department", null=True,
                                   on_delete=models.PROTECT)
    employees = models.ManyToManyField('self', blank=True)
    advisors = models.ManyToManyField("patients.Patients", blank=True)
    is_active = models.BooleanField(default=True)


class Practice(TimeStampedModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    tagline = models.CharField(max_length=256, null=True, blank=True)
    specialisation = models.CharField(max_length=524, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    locality = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=524, blank=True, null=True)
    city = models.CharField(max_length=524, blank=True, null=True)
    state = models.CharField(max_length=524, blank=True, null=True)
    pincode = models.PositiveIntegerField(null=True, blank=True)
    contact = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    website = models.CharField(max_length=256, blank=True, null=True)
    gstin = models.CharField(max_length=64, blank=True, null=True)
    logo = models.CharField(max_length=2000, blank=True, null=True)
    language = models.CharField(max_length=2000, blank=True, null=True)
    reg_city = models.ForeignKey("patients.City", blank=True, null=True, on_delete=models.PROTECT)
    reg_state = models.ForeignKey("patients.State", blank=True, null=True, on_delete=models.PROTECT)
    reg_country = models.ForeignKey("patients.Country", blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    hide_cancelled_invoice = models.BooleanField(default=False)
    hide_cancelled_return = models.BooleanField(default=False)
    hide_cancelled_payment = models.BooleanField(default=False)
    hide_cancelled_proforma = models.BooleanField(default=False)
    payment_prefix = models.CharField(max_length=64, blank=True, null=True)
    invoice_prefix = models.CharField(max_length=64, blank=True, null=True)
    return_prefix = models.CharField(max_length=64, blank=True, null=True)
    proforma_prefix = models.CharField(max_length=64, blank=True, null=True)
    default_doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)

    def __unicode__(self):
        return "%s" % (self.name)


class PracticeCalenderSettings(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    today_first_day = models.BooleanField(default=False)
    is_two_sessions = models.BooleanField(default=False)
    calendar_slot = models.PositiveSmallIntegerField(blank=True, null=True)
    visting_hour_same_week = models.BooleanField(default=False)
    first_start_time = models.TimeField(blank=True, null=True)
    second_start_time = models.TimeField(blank=True, null=True)
    second_end_time = models.TimeField(blank=True, null=True)
    first_end_time = models.TimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    monday = models.BooleanField(default=False)
    is_two_sessions_monday = models.BooleanField(default=False)
    first_start_time_monday = models.TimeField(blank=True, null=True)
    second_start_time_monday = models.TimeField(blank=True, null=True)
    second_end_time_monday = models.TimeField(blank=True, null=True)
    first_end_time_monday = models.TimeField(blank=True, null=True)
    tuesday = models.BooleanField(default=False)
    is_two_sessions_tuesday = models.BooleanField(default=False)
    first_start_time_tuesday = models.TimeField(blank=True, null=True)
    second_start_time_tuesday = models.TimeField(blank=True, null=True)
    second_end_time_tuesday = models.TimeField(blank=True, null=True)
    first_end_time_tuesday = models.TimeField(blank=True, null=True)
    wednesday = models.BooleanField(default=False)
    is_two_sessions_wednesday = models.BooleanField(default=False)
    first_start_time_wednesday = models.TimeField(blank=True, null=True)
    second_start_time_wednesday = models.TimeField(blank=True, null=True)
    second_end_time_wednesday = models.TimeField(blank=True, null=True)
    first_end_time_wednesday = models.TimeField(blank=True, null=True)
    thursday = models.BooleanField(default=False)
    is_two_sessions_thursday = models.BooleanField(default=False)
    first_start_time_thursday = models.TimeField(blank=True, null=True)
    second_start_time_thursday = models.TimeField(blank=True, null=True)
    second_end_time_thursday = models.TimeField(blank=True, null=True)
    first_end_time_thursday = models.TimeField(blank=True, null=True)
    friday = models.BooleanField(default=False)
    is_two_sessions_friday = models.BooleanField(default=False)
    first_start_time_friday = models.TimeField(blank=True, null=True)
    second_start_time_friday = models.TimeField(blank=True, null=True)
    second_end_time_friday = models.TimeField(blank=True, null=True)
    first_end_time_friday = models.TimeField(blank=True, null=True)
    saturday = models.BooleanField(default=False)
    is_two_sessions_saturday = models.BooleanField(default=False)
    first_start_time_saturday = models.TimeField(blank=True, null=True)
    second_start_time_saturday = models.TimeField(blank=True, null=True)
    second_end_time_saturday = models.TimeField(blank=True, null=True)
    first_end_time_saturday = models.TimeField(blank=True, null=True)
    sunday = models.BooleanField(default=False)
    is_two_sessions_sunday = models.BooleanField(default=False)
    first_start_time_sunday = models.TimeField(blank=True, null=True)
    second_start_time_sunday = models.TimeField(blank=True, null=True)
    second_end_time_sunday = models.TimeField(blank=True, null=True)
    first_end_time_sunday = models.TimeField(blank=True, null=True)


class AppointmentCategory(TimeStampedModel):
    colour = models.CharField(max_length=256, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticeStaffRelation(TimeStampedModel):
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class VisitingTime(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    doctor = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    is_two_sessions = models.BooleanField(default=False)
    visting_hour_same_week = models.BooleanField(default=False)
    first_start_time = models.TimeField(blank=True, null=True)
    second_start_time = models.TimeField(blank=True, null=True)
    second_end_time = models.TimeField(blank=True, null=True)
    first_end_time = models.TimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    monday = models.BooleanField(default=False)
    is_two_sessions_monday = models.BooleanField(default=False)
    first_start_time_monday = models.TimeField(blank=True, null=True)
    second_start_time_monday = models.TimeField(blank=True, null=True)
    second_end_time_monday = models.TimeField(blank=True, null=True)
    first_end_time_monday = models.TimeField(blank=True, null=True)
    tuesday = models.BooleanField(default=False)
    is_two_sessions_tuesday = models.BooleanField(default=False)
    first_start_time_tuesday = models.TimeField(blank=True, null=True)
    second_start_time_tuesday = models.TimeField(blank=True, null=True)
    second_end_time_tuesday = models.TimeField(blank=True, null=True)
    first_end_time_tuesday = models.TimeField(blank=True, null=True)
    wednesday = models.BooleanField(default=False)
    is_two_sessions_wednesday = models.BooleanField(default=False)
    first_start_time_wednesday = models.TimeField(blank=True, null=True)
    second_start_time_wednesday = models.TimeField(blank=True, null=True)
    second_end_time_wednesday = models.TimeField(blank=True, null=True)
    first_end_time_wednesday = models.TimeField(blank=True, null=True)
    thursday = models.BooleanField(default=False)
    is_two_sessions_thursday = models.BooleanField(default=False)
    first_start_time_thursday = models.TimeField(blank=True, null=True)
    second_start_time_thursday = models.TimeField(blank=True, null=True)
    second_end_time_thursday = models.TimeField(blank=True, null=True)
    first_end_time_thursday = models.TimeField(blank=True, null=True)
    friday = models.BooleanField(default=False)
    is_two_sessions_friday = models.BooleanField(default=False)
    first_start_time_friday = models.TimeField(blank=True, null=True)
    second_start_time_friday = models.TimeField(blank=True, null=True)
    second_end_time_friday = models.TimeField(blank=True, null=True)
    first_end_time_friday = models.TimeField(blank=True, null=True)
    saturday = models.BooleanField(default=False)
    is_two_sessions_saturday = models.BooleanField(default=False)
    first_start_time_saturday = models.TimeField(blank=True, null=True)
    second_start_time_saturday = models.TimeField(blank=True, null=True)
    second_end_time_saturday = models.TimeField(blank=True, null=True)
    first_end_time_saturday = models.TimeField(blank=True, null=True)
    sunday = models.BooleanField(default=False)
    is_two_sessions_sunday = models.BooleanField(default=False)
    first_start_time_sunday = models.TimeField(blank=True, null=True)
    second_start_time_sunday = models.TimeField(blank=True, null=True)
    second_end_time_sunday = models.TimeField(blank=True, null=True)
    first_end_time_sunday = models.TimeField(blank=True, null=True)


class Taxes(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=512, null=True, blank=True)
    tax_value = models.FloatField(max_length=256, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ProcedureCatalog(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, null=True, blank=True)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    cost = models.FloatField(blank=True, null=True)
    cost_with_tax = models.FloatField(blank=True, null=True)
    under = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name='parent')
    default_notes = models.TextField(null=True, blank=True)
    taxes = models.ManyToManyField(Taxes, related_name="procedure_normal_tax", blank=True)
    state_taxes = models.ManyToManyField(Taxes, related_name="procedure_other_state_tax", blank=True)
    is_active = models.BooleanField(default=True)


class PaymentModes(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    mode = models.CharField(max_length=256, null=True, blank=True)
    payment_type = models.CharField(max_length=256, null=True, blank=True)
    fee = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class PracticeOffers(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    code = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    discount = models.PositiveSmallIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=256, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class PracticeReferer(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticeComplaints(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Observations(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Diagnoses(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Investigations(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Treatmentnotes(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Filetags(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Medication(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Communications(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    contact_number = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    sms_language = models.CharField(max_length=256, blank=True, null=True)
    sms_clinic_name = models.CharField(max_length=1024, blank=True, null=True)
    appointment_confirmation_sms = models.BooleanField(default=True)
    appointment_confirmation_text = models.TextField(blank=True, null=True)
    appointment_cancellation_sms = models.BooleanField(default=True)
    appointment_cancellation_text = models.TextField(blank=True, null=True)
    appointment_reminder_sms = models.BooleanField(default=True)
    appointment_reminder_text = models.TextField(blank=True, null=True)
    appointment_reminder_day_before_time = models.TimeField(blank=True, null=True)
    appointment_reminder_day_before = models.BooleanField(default=True)
    send_on_day_of_appointment = models.BooleanField(default=True)
    send_on_day_before_appointment = models.BooleanField(default=True)
    follow_up_reminder_sms = models.BooleanField(default=True)
    follow_up_reminder_text = models.TextField(blank=True, null=True)
    send_follow_up_reminder_time = models.PositiveIntegerField(blank=True, null=True)
    payment_sms = models.BooleanField(default=False)
    payment_text = models.TextField(blank=True, null=True)
    birthday_wish_sms = models.BooleanField(default=False)
    anniversary_wish_sms = models.BooleanField(default=False)
    medicine_renew_sms = models.BooleanField(default=False)
    medicine_renew_text = models.TextField(blank=True, null=True)
    promo_code_value_text = models.CharField(max_length=524, blank=True, null=True)
    promo_code_percent_text = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s" % (self.contact_number)


class EmailCommunications(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    contact_number = models.CharField(max_length=256, blank=True, null=True)
    email = models.CharField(max_length=256, blank=True, null=True)
    email_clinic_name = models.CharField(max_length=256, blank=True, null=True)
    clinic_logo = models.CharField(max_length=256, blank=True, null=True)
    logo = models.CharField(max_length=256, blank=True, null=True)
    title = models.CharField(max_length=1024, blank=True, null=True)
    footer_text = models.CharField(max_length=1024, blank=True, null=True)
    appointment_confirmation_email = models.BooleanField(default=True)
    appointment_cancellation_email = models.BooleanField(default=True)
    appointment_reminder_email = models.BooleanField(default=True)
    send_on_day_of_appointment = models.BooleanField(default=True)
    send_before_day_of_appointment = models.BooleanField(default=True)
    followup_reminder_email = models.BooleanField(default=True)
    birthday_wish_email = models.BooleanField(default=True)
    lab_order_confirmation_email = models.BooleanField(default=True)
    anniversary_wish_email = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)


class LabTestCatalog(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class LabPanel(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    cost = models.IntegerField(blank=True, null=True)
    tests = models.ManyToManyField(LabTestCatalog, blank=True)
    is_active = models.BooleanField(default=True)


class DrugType(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class DrugUnit(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class DrugCatalog(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    unit = models.ForeignKey(DrugUnit, blank=True, null=True, on_delete=models.PROTECT)
    drug_type = models.ForeignKey(DrugType, blank=True, null=True, on_delete=models.PROTECT)
    strength = models.IntegerField(blank=True, null=True)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ExpenseType(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Vendor(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=1024, blank=True, null=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Expenses(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    expense_date = models.DateField(blank=True, null=True)
    expense_type = models.ForeignKey(ExpenseType, blank=True, null=True, on_delete=models.PROTECT)
    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.PROTECT)
    payment_mode = models.ForeignKey(PaymentModes, blank=True, null=True, on_delete=models.PROTECT)
    amount = models.FloatField(blank=True, null=True)
    remark = models.CharField(max_length=500, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticeUserPermissions(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=2000, blank=True, null=True)
    codename = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticePrintSettings(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    type = models.CharField(max_length=100, blank=True, null=True)
    sub_type = models.CharField(max_length=100, blank=True, null=True)
    page_size = models.CharField(max_length=100, blank=True, null=True)
    page_orientation = models.CharField(max_length=100, blank=True, null=True)
    page_print_type = models.CharField(max_length=100, blank=True, null=True)
    page_margin_top = models.CharField(max_length=100, blank=True, null=True)
    page_margin_left = models.CharField(max_length=100, blank=True, null=True)
    page_margin_right = models.CharField(max_length=100, blank=True, null=True)
    page_margin_bottom = models.CharField(max_length=100, blank=True, null=True)
    header_include = models.BooleanField(default=True)
    header_text = models.CharField(max_length=2000, blank=True, null=True)
    header_left_text = models.CharField(max_length=2000, blank=True, null=True)
    header_right_text = models.CharField(max_length=2000, blank=True, null=True)
    logo_include = models.BooleanField(default=True)
    logo_path = models.CharField(max_length=2000, blank=True, null=True)
    logo_type = models.CharField(max_length=100, blank=True, null=True)
    logo_alignment = models.CharField(max_length=100, blank=True, null=True)
    footer_margin_top = models.CharField(max_length=100, blank=True, null=True)
    footer_text = models.CharField(max_length=2000, blank=True, null=True)
    footer_left_text = models.CharField(max_length=2000, blank=True, null=True)
    footer_right_text = models.CharField(max_length=2000, blank=True, null=True)
    patient_details = models.BooleanField(default=True)
    exclude_history = models.BooleanField(default=False)
    exclude_patient_id = models.BooleanField(default=False)
    exclude_address = models.BooleanField(default=False)
    exclude_email = models.BooleanField(default=False)
    exclude_phone = models.BooleanField(default=False)
    exclude_blood_group = models.BooleanField(default=False)
    exclude_gender_dob = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Advice(models.Model):
    details = models.CharField(max_length=1024, null=True, blank=True)


class DrugCatalogTemplate(TimeStampedModel):
    from ..inventory.models import InventoryItem
    inventory = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    dosage = models.CharField(max_length=1024, blank=True, null=True)
    frequency = models.CharField(max_length=1024, blank=True, null=True)
    before_food = models.BooleanField(default=False)
    after_food = models.BooleanField(default=False)
    duration = models.IntegerField(blank=True, null=True)
    duration_type = models.CharField(max_length=10, blank=True, null=True)


class PrescriptionTemplate(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    drugs = models.ManyToManyField(DrugCatalogTemplate, blank=True)
    labs = models.ManyToManyField(LabTestCatalog, blank=True)
    follow_up = models.BooleanField(default=False)
    input_time = models.IntegerField(null=True, blank=True)
    time_type = models.CharField(max_length=10, null=True, blank=True)
    advice = models.BooleanField(default=False)
    advice_data = models.ManyToManyField(Advice, blank=True)
    is_active = models.BooleanField(default=True)


class RoomTypeSettings(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    normal_seats = models.PositiveIntegerField(null=True, blank=True)
    tatkal_seats = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class BedBookingPackage(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)
    normal_price = models.FloatField(null=True, blank=True)
    tatkal_price = models.FloatField(null=True, blank=True)
    taxes = models.ManyToManyField(Taxes, related_name="bed_normal_tax", blank=True)
    state_taxes = models.ManyToManyField(Taxes, related_name="bed_other_state_tax", blank=True)
    normal_tax_value = models.FloatField(null=True, blank=True)
    tatkal_tax_value = models.FloatField(null=True, blank=True)
    no_of_days = models.PositiveIntegerField(null=True, blank=True)
    image = models.CharField(max_length=1024, null=True, blank=True)
    room = models.ForeignKey(RoomTypeSettings, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class MedicineBookingPackage(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    under = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name='parent')
    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.CharField(max_length=1024, blank=True, null=True)
    taxes = models.ManyToManyField(Taxes, related_name="medicine_normal_tax", blank=True)
    state_taxes = models.ManyToManyField(Taxes, related_name="medicine_other_state_tax", blank=True)
    price = models.FloatField(null=True, blank=True)
    no_of_days = models.PositiveIntegerField(null=True, blank=True)
    image = models.CharField(max_length=1024, null=True, blank=True)
    tax_value = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Membership(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    fee = models.FloatField(blank=True, null=True)
    benefit = models.FloatField(blank=True, null=True)
    validity = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Registration(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    fee = models.FloatField(blank=True, null=True)
    validity = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticeVitalSign(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    temperature_unit = models.CharField(max_length=1024, blank=True, null=True)
    temperature_method = models.CharField(max_length=1024, blank=True, null=True)
    blood_pressure_method = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class OtherDiseases(models.Model):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ActivityLog(TimeStampedModel):
    from ..patients.models import Patients
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    staff = models.ForeignKey(PracticeStaff, blank=True, null=True, on_delete=models.PROTECT)
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    component = models.CharField(max_length=1024, blank=True, null=True)
    sub_component = models.CharField(max_length=1024, blank=True, null=True)
    activity = models.CharField(max_length=1024, blank=True, null=True, choices=ACTIVITY_OPTIONS)
    os = models.CharField(max_length=1024, blank=True, null=True)
    agent = models.CharField(max_length=1024, blank=True, null=True)
    application = models.CharField(max_length=1024, blank=True, null=True)
    extra = models.CharField(max_length=1024, blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT, related_name="Current_User")
    record_created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT,
                                          related_name="Previous_User")
    is_active = models.BooleanField(default=True)


class PushNotifications(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT, related_name="notification_user")
    device = models.CharField(max_length=1024, blank=True, null=True)
    application = models.CharField(max_length=1024, blank=True, null=True)
    title = models.CharField(max_length=1024, blank=True, null=True)
    body = models.CharField(max_length=1024, blank=True, null=True)
    icon = models.CharField(max_length=1024, blank=True, null=True)
    image_link = models.CharField(max_length=1024, blank=True, null=True)
    open_screen = models.CharField(max_length=1024, blank=True, null=True)
    detail_id = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Permissions(TimeStampedModel):
    codename = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PermissionGroup(TimeStampedModel):
    group_name = models.CharField(max_length=1024, blank=True, null=True)
    group_description = models.CharField(max_length=1024, blank=True, null=True)
    permissions = models.ManyToManyField(Permissions, blank=True)
    is_global = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class NoticeBoard(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(PracticeStaff, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    

