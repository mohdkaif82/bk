from datetime import datetime, timedelta

from .utils.timezone import now_local

CONST_PATIENT_PROFILE = "Patient Profile"
CONST_ERP_SETTINGS = 'ERP Settings'
CONST_REPORT_MAIL = "MailReports"
CONST_PRACTICE_CALENDAR = 'Practice Calendar'
CONST_PATIENT_EMR = 'Patient EMR'
CONST_PATIENT_BILLING = 'Patient Billing'
CONST_ERP_REPORTS = 'ERP Reports'
CONST_BACK_OFFICE = 'Back Office'
CONST_MEETING = 'Meeting'
CONST_WEB_ADMIN = 'Web Admin'
CONST_TASK_TRACK = 'Task Track'
CONST_STAFF = 'Staff'
CONST_ADVISOR = 'Advisor'
CONST_PATIENTS = 'Patient'
CONST_WEB = 'Web'
CONST_IOS = 'iOS'
CONST_ANDROID = 'Android'

ROLES_PERMISSIONS = [
    {'codename': 'SettingsPracticeDetail', 'name': 'Settings || Practice Detail', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsCommunincations', 'name': 'Settings || Communincations', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsCalendar', 'name': 'Settings || Calendar', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsPracticeStaff', 'name': 'Settings || Practice Staff', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsProcedureCatalog', 'name': 'Settings || Procedure Catalog', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsBilling', 'name': 'Settings || Billing', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsLoyalty', 'name': 'Settings || Loyalty', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsEMR', 'name': 'Settings || EMR', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsPrescriptions', 'name': 'Settings || Prescriptions', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsLabs', 'name': 'Settings || Labs', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsPrintouts', 'name': 'Settings || Printouts', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsMedicalHistory', 'name': 'Settings || Medical History', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsExpenseTypes', 'name': 'Settings || Expense Types', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsMLMSettings', 'name': 'Settings || MLM', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsMLMCompensationSettings', 'name': 'Settings || MLM Compensation', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsRoomTypes', 'name': 'Settings || Room Types', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsBedPackages', 'name': 'Settings || Bed Packages', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsMedicinePackages', 'name': 'Settings || Medicine Packages', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsDiseaseList', 'name': 'Settings || Disease List', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsAgentRoles', 'name': 'Settings || Advisor Roles', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsAgents', 'name': 'Settings || Advisor', 'module': CONST_ERP_SETTINGS},
    {'codename': 'ViewCalendar', 'name': 'Calendar', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'BlockCalendar', 'name': 'Block Calendar', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'AddAppointment', 'name': 'Add Appointment', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'EditAppointment', 'name': 'Edit Appointment', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'ChangeAppointmentStatus', 'name': 'Change Appointment Status', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'AddWalkinAppointment', 'name': 'Add Walk In Appointment', 'module': CONST_PRACTICE_CALENDAR},
    {'codename': 'AddPatient', 'name': 'Add Patient', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'EditPatient', 'name': 'Edit Patient', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'ViewPatient', 'name': 'View Patient', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'DeletePatient', 'name': 'Delete Patient', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'MergePatients', 'name': 'Merge Patients', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'PatientAppointments', 'name': 'Patients || Appointments', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'PatientCommunications', 'name': 'Patients || Communications', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'PatientBookings', 'name': 'Patients || Bookings', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientVitalSigns', 'name': 'Patients || Vital Signs', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientClinicalNotes', 'name': 'Patients || Clinical Notes', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientTreatmentPlans', 'name': 'Patients || Treatment Plans', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientCompletedProcedure', 'name': 'Patients || Completed Procedure', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientFiles', 'name': 'Patients || Files', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientPrescriptions', 'name': 'Patients || Prescriptions', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientTimeline', 'name': 'Patients || Timeline', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientLabOrders', 'name': 'Patients || Lab Orders', 'module': CONST_PATIENT_EMR},
    {'codename': 'PatientInvoices', 'name': 'Patients || Invoices', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientPayments', 'name': 'Patients || Payments', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientAddEditInvoices', 'name': 'Patients || Add/Edit Invoices', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientAddEditPayments', 'name': 'Patients || Add/Edit Payments', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientReturns', 'name': 'Patients || Returns', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientAddEditReturns', 'name': 'Patients || Add/Edit Returns', 'module': CONST_PATIENT_BILLING},
    {'codename': 'PatientLedger', 'name': 'Patients || Ledger', 'module': CONST_PATIENT_BILLING},
    {'codename': 'EditPatientNotes', 'name': 'Patients || Edit Notes', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'DeletePatientNotes', 'name': 'Patients || Delete Notes', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'ReportsDailySummary', 'name': 'Reports || Daily Summary', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsIncome', 'name': 'Reports || Income', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsPayments', 'name': 'Reports || Payments', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsAppointments', 'name': 'Reports || Appointments', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsPatients', 'name': 'Reports || Patients', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsAmountDue', 'name': 'Reports || Amount Due', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsExpenses', 'name': 'Reports || Expenses', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsInventory', 'name': 'Reports || Inventory', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsEMR', 'name': 'Reports || EMR', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsInventoryRetail', 'name': 'Reports || Inventory Retail', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsMLMReport', 'name': 'Reports || MLM Report', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsBedBooking', 'name': 'Reports || Bed Booking', 'module': CONST_ERP_REPORTS},
    {'codename': 'ReportsSuggestions', 'name': 'Reports || Suggestions', 'module': CONST_ERP_REPORTS},
    {'codename': 'ViewExpenses', 'name': 'Back Office || View Expenses', 'module': CONST_BACK_OFFICE},
    {'codename': 'ExportExpenses', 'name': 'Back Office || Export Expenses', 'module': CONST_BACK_OFFICE},
    {'codename': 'EditExpenses', 'name': 'Back Office || Edit Expenses', 'module': CONST_BACK_OFFICE},
    {'codename': 'DeleteExpenses', 'name': 'Back Office || Delete Expenses', 'module': CONST_BACK_OFFICE},
    {'codename': 'ViewManufacturer', 'name': 'Back Office || View Manufacturer', 'module': CONST_BACK_OFFICE},
    {'codename': 'EditManufacturer', 'name': 'Back Office || Edit Manufacturer', 'module': CONST_BACK_OFFICE},
    {'codename': 'DeleteManufacturer', 'name': 'Back Office || Delete Manufacturer', 'module': CONST_BACK_OFFICE},
    {'codename': 'ExportManufacturer', 'name': 'Back Office || Export Manufacturer', 'module': CONST_BACK_OFFICE},
    {'codename': 'ViewVendor', 'name': 'Back Office || View Vendor', 'module': CONST_BACK_OFFICE},
    {'codename': 'EditVendor', 'name': 'Back Office || Edit Vendor', 'module': CONST_BACK_OFFICE},
    {'codename': 'DeleteVendor', 'name': 'Back Office || Delete Vendor', 'module': CONST_BACK_OFFICE},
    {'codename': 'ExportVendor', 'name': 'Back Office || Export Vendor', 'module': CONST_BACK_OFFICE},
    {'codename': 'ViewActivities', 'name': 'Back Office || View Activities', 'module': CONST_BACK_OFFICE},
    {'codename': 'ViewInventory', 'name': 'Inventory || View Inventory', 'module': CONST_BACK_OFFICE},
    {'codename': 'ExportInventory', 'name': 'Inventory || Export Inventory', 'module': CONST_BACK_OFFICE},
    {'codename': 'AddInventoryItem', 'name': 'Inventory || Add Inventory Item', 'module': CONST_BACK_OFFICE},
    {'codename': 'AddInventoryStock', 'name': 'Inventory || Add Stock', 'module': CONST_BACK_OFFICE},
    {'codename': 'ConsumeInventoryStock', 'name': 'Inventory || Consume Stock', 'module': CONST_BACK_OFFICE},
    {'codename': 'Labs', 'name': 'Labs', 'module': CONST_BACK_OFFICE},
]

GLOBAL_PERMISSIONS = [
    {'codename': 'WebAdmin', 'name': 'Web Admin', 'module': CONST_WEB_ADMIN},
    {'codename': 'PatientPhoneNumber', 'name': 'View Patient Phone Number', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'RelativePhoneNumber', 'name': 'View Relatives Phone Number', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'ViewPatientAddress', 'name': 'View Patient Address', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'ViewAllClinics', 'name': 'View Patients on All Clinics', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'ManagePatientPractice', 'name': 'Manage Patients on Clinics', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'PatientEmailId', 'name': 'View Patient Email Id', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'AddPatientRegistration', 'name': 'Patients || Add Registration', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'CancelPatientRegistration', 'name': 'Patients || Cancel Registration',
     'module': CONST_PATIENT_PROFILE},
    {'codename': CONST_REPORT_MAIL, 'name': 'Get Reports Over Mail', 'module': CONST_ERP_REPORTS},
    {'codename': "ReportsTaskTrack", 'name': 'Task Track Reports', 'module': CONST_ERP_REPORTS},
    {'codename': 'ViewMeeting', 'name': 'View Meeting', 'module': CONST_MEETING},
    {'codename': 'CreateMeeting', 'name': 'Create Meeting', 'module': CONST_MEETING},
    {'codename': 'UpdateMeeting', 'name': 'Update Meeting', 'module': CONST_MEETING},
    {'codename': 'DeleteMeeting', 'name': 'Delete Meeting', 'module': CONST_MEETING},
    {'codename': 'TaskHeads', 'name': 'Task Heads', 'module': CONST_TASK_TRACK},
    {'codename': 'AllRecurringTasks', 'name': 'All Recurring Tasks', 'module': CONST_TASK_TRACK},
    {'codename': 'MonthlyTaskTargets', 'name': 'Monthly Targets', 'module': CONST_TASK_TRACK},
    {'codename': 'SendMailToPatient', 'name': 'Send Mail To Patient', 'module': CONST_PATIENT_PROFILE},
    {'codename': 'SettingsAddress', 'name': 'Settings || Address', 'module': CONST_ERP_SETTINGS},
    {'codename': 'SettingsOtherSettings', 'name': 'Settings || Other Settings', 'module': CONST_ERP_SETTINGS},
]

CONST_WISH_SMS = {
    "HINDI": {
        "BIRTHDAY": "{{PATIENT}}, B.K. AROGYAM & RESEARCH PRIVATE LIMITED आपको जन्मदिन की ढेर सारी शुभ कामनायें देता है। आप हमेशा मुस्कुराते रहें।",
        "ANNIVERSARY": "{{PATIENT}}, B.K. AROGYAM & RESEARCH PRIVATE LIMITED आपको सालगिरह की ढेर सारी शुभ कामनायें देता है। आप हमेशा मुस्कुराते रहें।"
    },
    "ENGLISH": {
        "BIRTHDAY": "{{PATIENT}}, B.K. AROGYAM & RESEARCH PRIVATE LIMITED wishes you a very happy birthday. Have a happy smile today & forever.",
        "ANNIVERSARY": "Dear {{PATIENT}}, B.K. AROGYAM & RESEARCH PRIVATE LIMITED wishes you a very happy wedding anniversary! Wishing you & your spouse a happy & healthy life."
    }
}

CONFIG = {
    "config_blood_group": ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
    "config_sms_language": ["HINDI", "ENGLISH"],
    "config_android_build_version": 9,
    "config_android_patient_build_version": 4,
    "config_android_advisor_build_version": 10,
    "config_family_relation": [
        {'name': "Child", 'value': 'CHILD'},
        {'name': "Parent  ", 'value': 'PARENT'},
        {'name': "Brother/Sister", 'value': 'BROTHER/SISTER'},
        {'name': "Husband/Wife", 'value': 'HUSBAND/WIFE'},
        {'name': "Grandchild", 'value': 'GRANDCHILD'},
        {'name': "GrandParent", 'value': 'GRANDPARENT'},
        {'name': "Uncle/Aunt", 'value': 'UNCLE/AUNT'},
        {'name': "Nephew/Niece", 'value': 'NEPHEW/NIECE'},
        {'name': "Cousin", 'value': 'COUSIN'},
    ],
    "config_gender": [
        {'label': 'Female', 'value': 'female'},
        {'label': 'Male', 'value': 'male'},
        {'label': 'Other', 'value': 'other'},
    ],
    "config_dose_required": [
        {'label': 'twice daily', 'value': 'twice daily', 'quantity': 2},
        {'label': 'three times a day', 'value': 'three times a day', 'quantity': 3},
        {'label': 'four times a day', 'value': 'four times a day', 'quantity': 4},
        {'label': 'every four hours', 'value': 'every four hours', 'quantity': 6},
        {'label': 'as needed', 'value': 'as needed', 'quantity': 1},
        {'label': 'every 2 hour(s)', 'value': 'every 2 hour(s)', 'quantity': 12},
        {'label': 'every other hour', 'value': 'every other hour', 'quantity': 12},
        {'label': 'every day', 'value': 'every day', 'quantity': 1},
        {'label': 'every other day', 'value': 'every other day', 'quantity': 0.5},
    ],
    "config_durations_unit": [
        {'label': 'day(s)', 'value': 'day(s)'},
        {'label': 'week(s)', 'value': 'week(s)'},
        {'label': 'month(s)', 'value': 'month(s)'},
        {'label': 'year(s)', 'value': 'year(s)'},
    ],
    "config_call_types": ["Audio", "Video"],
    "config_call_response": ["Not Connected", "Converted", "Not Converted"],
    "config_coldcall_response": ["Not Connected", "Converted", "Not Converted"],
    "config_android_url": "https://play.google.com/store/apps/details?id=com.bkarogyam",
    "config_android_patient_url": "https://play.google.com/store/apps/details?id=com.bkpatient",
    "config_android_advisor_url": "https://play.google.com/store/apps/details?id=com.bkadvisor",
    "config_const_patients": CONST_PATIENTS,
    "config_const_advisors": CONST_ADVISOR,
    "config_const_staff": CONST_STAFF,
    "config_const_android": CONST_ANDROID,
    "config_const_ios": CONST_IOS,
    "config_const_web": CONST_WEB,
    "config_advisor_department": 14,
    "config_advisor_designation": 2,
    "config_advisor_contact": "Dear User,\n Please Contact 8081222333",
    "config_default_clinic_contact": "8081222333",
    "config_default_referal": "RITE1AC2",
    "config_default_referal_practice": 5,
    "config_default_advisor_role": None,
    "config_date_only": now_local(True),
    "config_date_time": now_local(),
    "config_wish_sms": CONST_WISH_SMS
}

CONST_CANCELLED = "Cancelled"
CONST_GLOBAL_PRACTICE = "BK Arogyam & Research Pvt. Ltd."

CONST_PATIENT_DATA = {
    "user": {
        "email": "",
        "mobile": "",
        "first_name": ""
    },
    "medical_history_data": [
        {
            "name": "medical"
        }
    ],
    "medical_membership_data": [],
    "gender": "male",
    "dob": "2010-05-12",
    "anniversary": "2019-04-16",
    "blood_group": "O+",
    "address": "murad nagar ghaziabad",
    "locality": "ghaziabad",
    "city": "sahibabad",
    "pincode": 201005
}

CONST_DOCTOR_DATA = {
    "user": {
        "email": "",
        "mobile": "",
        "first_name": ""
    }
}

CONST_APPOINTMENT_DATA = {
    "patient": {
        "user": {
            "first_name": "Shivam"
        },
        "custom_id": "BK16"
    },
    "practice_data": {
        "name": "BK Arogyam Delhi",
        "address": "Rohini East",
        "locality": "Near Metro Station",
        "city": "Delhi",
        "state": "Delhi",
        "country": "India",
        "pincode": "110011"
    },
    "schedule_at": "2020-05-08T10:26:52+05:30"
}

CONST_PRACTICE_DATA = {
    "id": 1,
    "name": "BK Arogyam Delhi",
    "email": "doctor@bkarogyam.com",
    "logo": "clinic-image/blogimage/2019/7/20/2019-07-20 07:35:46.469431+00:00/kidneycarelogo.png",
    "address": "Dwarka Phase 1",
    "locality": "Near XYZ Store",
    "city": "Delhi",
    "state": "Delhi",
    "country": "India",
    "pincode": 110011
}

CONST_VITAL_SIGN_DATA = {
    "date": "2019-06-01T10:00:00Z",
    "pulse": 90.0,
    "temperature": 98.3,
    "temperature_part": "Oral",
    "blood_pressure": "120/80",
    "position": "Sitting",
    "weight": 70.0,
    "resp_rate": 15.0,
    "is_active": True,
    "practice": 4,
    "patient": 2,
    "doctor": 16,
    "type": "Vital Signs"
}

CONST_MEDICAL_LEAVE_DATA = {
    "id": 1,
    "excuse_date_days": 1,
    "excused_duty": True,
    "excused_duty_from": datetime.today().date(),
    "excused_duty_to": datetime.today().date(),
    "excused_duty_from_session": "Morning",
    "excused_duty_to_session": "Evening",
    "fit_light_duty": True,
    "fit_light_duty_from": datetime.today().date(),
    "fit_light_duty_to": datetime.today().date(),
    "proof_attendance": True,
    "proof_attendance_date": datetime.today().date(),
    "proof_attendance_from": datetime.today().time(),
    "proof_attendance_to": (datetime.today() + timedelta(minutes=10)).time(),
    "notes": "This is a Sample Note.",
    "valid_court": False,
    "invalid_court": False,
    "no_mention": True,
    "date": "2019-06-01",
    "is_active": True
}

CONST_CLINICAL_NOTES_DATA = {
    "id": 9,
    "doctor": {
        "user": {
            "email": "",
            "mobile": "",
            "first_name": ""
        }
    },
    "is_active": True,
    "chief_complaints": "Sample Complaint$_$",
    "investigations": "Health Issues$_$",
    "diagnosis": "Sample Diagnosis$_$",
    "notes": "Patient notes$_$",
    "observations": "vomiting$_$",
    "date": "2019-06-01",
    "type": "Clinical Notes"
}

CONST_TREATMENT_PLAN_DATA = {
    "treatment_plans": [
        {
            "procedure": {
                "name": "Sample Treatment Category 1"
            },
            "quantity": 1,
            "default_notes": "Sample Treatment Plan Description<br>Teeth: 13|11|10",
            "cost": 1000,
            "is_completed": True,
            "discount": 10,
            "discount_type": "%"
        },
        {
            "procedure": {
                "name": "Sample Treatment Category 2"
            },
            "quantity": 1,
            "default_notes": "Sample Treatment Plan Description<br>Teeth: 23|22",
            "cost": 700,
            "is_completed": True,
            "discount": None,
            "discount_type": "%"
        }
    ],
    "doctor": {
        "user": {
            "email": "remercuras@gmail.com",
            "mobile": "8090387724",
            "first_name": "ritesh"
        },
    },
    "date": "2019-06-01",
    "is_active": True,
    "summary_amount": {
        "total_amount": 1700,
        "discount": 100.0,
        "grand_total": 1600
    },
    "type": "Procedures"
}

CONST_PRESCRIPTION_DATA = {
    "drugs": [
        {
            "inventory": {
                "strength_type_data": {
                    "name": "mg",
                },
                "drug_type_data": {
                    "name": "Tablet"
                },
                "total_quantity": 1,
                "name": "Crocin",
                "instructions": "Take with normal water",
                "strength": 100.0,
                "is_active": True,
                "maintain_inventory": False,
                "practice": None,
                "manufacturer": None,
                "vendor": None,
                "taxes": []
            },
            "name": "Crocin",
            "quantity": 5,
            "unit": 1,
            "dosage": None,
            "frequency": "twice daily",
            "duration": 5,
            "duration_type": "day(s)",
            "before_food": True,
            "after_food": False,
            "instruction": "Take One Tablet daily"
        },
        {
            "id": 6,
            "inventory": {
                "strength_type_data": {
                    "name": "mg",
                },
                "drug_type_data": {
                    "name": "Tablet"
                },
                "name": "Pudin Hara",
                "instructions": "Take 2 Tablets daily",
                "strength": 100.0
            },
            "name": "Pudin Hara",
            "quantity": 4,
            "unit": 2,
            "dosage": None,
            "frequency": "twice daily",
            "duration": 2,
            "duration_type": "day(s)",
            "before_food": True,
            "after_food": False,
            "instruction": "Take 2 Tablets daily"
        }
    ],
    "labs": [],
    "doctor": {
        "user": {
            "email": "remercuras@gmail.com",
            "mobile": "8090387724",
            "first_name": "Ritesh Chaurasia"
        }
    },
    "date": "2019-06-01",
    "follow_up": False,
    "days": None,
    "input_time": None,
    "time_type": None,
    "advice": False,
    "doctor_notes": "This is a Sample Instruction",
    "is_active": True,
    "patient": 11,
    "type": "Prescriptions"
}

CONST_PAYMENTS_DATA = {
    "id": 3,
    "payment_id": "SAMPLE/RCPT/3",
    "invoices": [
        {
            "id": 1,
            "invoice": {
                "id": 42,
                "invoice_id": "SAMPLE/INV/42",
                "payments_data": 25.0,
                "procedure": [
                    {
                        "doctor_data": {
                            "user": {
                                "email": "admin@admin.com",
                                "mobile": "9090909090",
                                "first_name": "Ritesh Chaurasia"
                            }
                        },
                        "name": "Procedure Name",
                        "unit_cost": 105.0,
                        "discount": 5.0,
                        "discount_type": "INR",
                        "unit": 1,
                        "default_notes": None,
                        "is_active": True,
                        "date": None,
                        "total": 109.0,
                        "tax_value": 9.0,
                        "discount_value": 5.0,
                    }
                ],
                "inventory": [
                    {
                        "doctor_data": {
                            "user": {
                                "email": "admin@admin.com",
                                "mobile": "9090909090",
                                "first_name": "Ritesh Chaurasia"
                            }
                        },
                        "inventory_item_data": {
                            "name": "Test",
                            "code": "",
                            "re_order_level": "5",
                            "retail_price": 100.0,
                            "item_type": "Drug",
                            "perscribe_this": True,
                            "stocking_unit": "Bottle",
                            "instructions": "Hello",
                        },
                        "name": "kishan yajona",
                        "unit": 1,
                        "unit_cost": 100.0,
                        "discount": 0.0,
                        "discount_type": "%",
                        "instruction": "s",
                        "is_active": True,
                        "total": 109.0,
                        "tax_value": 9.0,
                        "discount_value": 0.0,
                        "batch_number": None,
                        "date": "2019-05-22",
                        "inventory": 12,
                        "drug_unit": None,
                        "drug_type": None,
                        "offers": 1,
                        "doctor": 16,
                        "taxes": [
                            1
                        ]
                    }
                ],
                "cost": 205.0,
                "discount": 5.0,
                "taxes": 18.0,
                "total": 218.0,
                "is_pending": False,
                "is_active": True,
                "is_cancelled": False,
                "practice": 4,
                "patient": 2,
                "prescription": []
            },
            "pay_amount": 25.0,
            "is_active": True
        }
    ],
    "bank": "SBI",
    "number": "1234",
    "total": 25.0,
    "is_advance": False,
    "is_active": True,
    "is_cancelled": False,
    "date": "2019-06-01",
    "payment_mode": 3
}

CONST_RETURN_DATA = {
    "id": 7,
    "practice_data": {
        "id": 1,
        "name": "BK Arogyam Delhi",
        "email": "doctor@bkarogyam.com",
        "logo": "clinic-image/blogimage/2019/7/20/2019-07-20 07:35:46.469431+00:00/kidneycarelogo.png"
    },
    "staff_data": None,
    "return_id": "DEL/RET7",
    "patient_data": {
        "id": 4,
        "user": {
            "id": 7,
            "email": "nsniteshsharma47@gmail.com",
            "mobile": "8882065182",
            "first_name": "Nitish",
            "referer_code": "",
            "is_active": True,
            "last_login": "2019-08-19T10:55:03.063922Z",
            "is_superuser": False
        },
        "gender": "male"
    },
    "procedure": [],
    "inventory": [
        {
            "id": 7,
            "created_at": "2019-08-24T19:51:55.348346Z",
            "modified_at": "2019-08-24T19:51:55.522890Z",
            "name": "Test Medicine",
            "strength": None,
            "dosage": None,
            "frequency": None,
            "unit": 1,
            "unit_cost": 95.2380952380952,
            "discount": None,
            "discount_type": "%",
            "instruction": None,
            "is_active": True,
            "total": 104.761904761905,
            "tax_value": 9.52380952380952,
            "discount_value": 0.0,
            "batch_number": "ABC",
            "inventory": 2,
            "inventory_inv": 12,
            "drug_unit": None,
            "drug_type": None,
            "offers": None,
            "doctor": 2,
            "stock": 39,
            "taxes": [
                2,
                11,
                12
            ]
        }
    ],
    "created_at": "2019-08-24T19:51:55.177900Z",
    "modified_at": "2019-08-24T19:51:55.525325Z",
    "bank": None,
    "number": None,
    "is_active": True,
    "is_cancelled": False,
    "date": "2019-08-23",
    "cost": 95.2380952380952,
    "discount": 0.0,
    "taxes": 9.52380952380952,
    "total": 104.761904761905,
    "return_value": 0.0,
    "practice": 1,
    "patient": 4,
    "staff": None,
    "return_mode": None,
    "invoice": 24
}

CONST_INVOICE_DATA = {
    "id": 42,
    "invoice_id": "SAMPLE/INV/42",
    "payments_data": None,
    "procedure": [
        {
            "doctor_data": {
                "user": {
                    "email": "",
                    "mobile": "",
                    "first_name": ""
                }
            },
            "name": "Procedure Name",
            "unit_cost": 105.0,
            "discount": 5.0,
            "discount_type": "INR",
            "unit": 1,
            "default_notes": None,
            "is_active": True,
            "date": None,
            "total": 109.0,
            "tax_value": 9.0,
            "discount_value": 5.0,
        }
    ],
    "inventory": [
        {
            "doctor_data": {
                "user": {
                    "email": "admin@admin.com",
                    "mobile": "9090909090",
                    "first_name": "Ritesh Chaurasia"
                }
            },
            "inventory_item_data": {
                "name": "Test",
                "code": "",
                "re_order_level": "5",
                "retail_price": 100.0,
                "item_type": "Drug",
                "perscribe_this": True,
                "stocking_unit": "Bottle",
                "instructions": "Hello",
            },
            "name": "Test",
            "unit": 1,
            "unit_cost": 100.0,
            "discount": 0.0,
            "discount_type": "%",
            "instruction": "s",
            "is_active": True,
            "total": 109.0,
            "tax_value": 9.0,
            "discount_value": 0.0,
            "batch_number": None,
            "date": "2019-05-22",
            "inventory": 12,
            "drug_unit": None,
            "drug_type": None,
            "offers": 1,
            "doctor": 16,
            "taxes": [
                1
            ]
        }
    ],
    "cost": 205.0,
    "discount": 5.0,
    "taxes": 18.0,
    "total": 218.0,
    "date": "2019-06-01",
    "is_pending": False,
    "is_active": True,
    "is_cancelled": False,
    "practice": 4,
    "patient": 2,
    "prescription": [],
    "type": "Invoices"
}

CONST_LAB_ORDER_DATA = {
    "labs": [
        {
            "name": "Sample Test 1",
            "cost": 100.0,
            "instruction": "This is a Sample Instruction.",
            "is_active": True
        },
        {
            "name": "Sample Test 2",
            "cost": 200.0,
            "instruction": "This is a Sample Instruction.",
            "is_active": True
        }
    ],
    "doctor": {
        "user": {
            "email": "remercuras@gmail.com",
            "mobile": "8090387724",
            "first_name": "Ritesh Chaurasia"
        }
    },
    "date": "2019-04-21"
}

CONST_BOOKING_DATA = {}

CONST_CASE_SHEET_DATA = [
    CONST_CLINICAL_NOTES_DATA,
    CONST_INVOICE_DATA,
    CONST_PRESCRIPTION_DATA,
    CONST_TREATMENT_PLAN_DATA,
    CONST_VITAL_SIGN_DATA
]

CONST_MEMBERSHIP = "Membership Amount."
CONST_REGISTRATION = "Registration Amount"

CONST_ORDER_PREFIX = "ORD"

CONST_ORDER_PLACED_SMS = "Dear {0}({1}),\n\nYour Order is Placed Successfully. Your Order ID is {2}. Amount Paid: INR{3}. For more details please check your email ID.\n\nThank You,\nB.K. AROGYAM & RESEARCH PRIVATE LIMITED"

CONST_APPOINTMENT_SUMMARY_SMS = "Dear Dr. {0},\n\nYour today's({1}) upcoming appointments summary at B.K. AROGYAM & RESEARCH PRIVATE LIMITED:\n\n"

CONST_APPOINTMENT_SUMMARY_STAFF_SMS = "Today's({0}) upcoming appointments summary practice wise at B.K. AROGYAM & RESEARCH PRIVATE LIMITED:\n\n"
