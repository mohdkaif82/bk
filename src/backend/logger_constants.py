from .appointment.models import Appointment, BlockCalendar
from .inventory.models import InventoryItem
from .meeting.models import Meeting
from .muster_roll.models import HrSettings, UserTasks, TaskTemplates, TaskComments
from .patients.models import PatientVitalSigns, PatientClinicNotes, PatientProcedure, PatientFile, \
    PatientPrescriptions, PatientMembership, PatientRegistration
from .patients.models import Patients, PatientInvoices, PatientPayment, ReturnPayment, Reservations
from .practice.models import Communications, PracticeStaff, Practice, PracticeCalenderSettings, \
    AppointmentCategory, VisitingTime, Taxes, ProcedureCatalog, PaymentModes, PracticeOffers, MedicineBookingPackage, \
    PracticeUserPermissions, PracticePrintSettings, Expenses, Membership, BedBookingPackage

CONST_LOG_GENERATOR = [
    {
        "model_name": Communications,
        "Category": "Settings",
        "SubCategory": "SMS Settings"
    },
    {
        "model_name": PracticeStaff,
        "Category": "Settings",
        "SubCategory": "Staff/Doctor"
    },
    {
        "model_name": HrSettings,
        "Category": "Settings",
        "SubCategory": "Other Settings"
    },
    {
        "model_name": Practice,
        "Category": "Settings",
        "SubCategory": "Practice Profile"
    },
    {
        "model_name": PracticeCalenderSettings,
        "Category": "Settings",
        "SubCategory": "Calendar"
    },
    {
        "model_name": AppointmentCategory,
        "Category": "Settings",
        "SubCategory": "Appointment Category"
    },
    {
        "model_name": VisitingTime,
        "Category": "Settings",
        "SubCategory": "Doctor Visiting Time"
    },
    {
        "model_name": Taxes,
        "Category": "Settings",
        "SubCategory": "Taxes"
    },
    {
        "model_name": ProcedureCatalog,
        "Category": "Settings",
        "SubCategory": "Procedure"
    },
    {
        "model_name": PaymentModes,
        "Category": "Settings",
        "SubCategory": "Payment Modes"
    },
    {
        "model_name": PracticeOffers,
        "Category": "Settings",
        "SubCategory": "Offers"
    },
    {
        "model_name": PracticeUserPermissions,
        "Category": "Settings",
        "SubCategory": "Staff Permissions"
    },
    {
        "model_name": PracticePrintSettings,
        "Category": "Settings",
        "SubCategory": "Print Settings"
    },
    {
        "model_name": Expenses,
        "Category": "Settings",
        "SubCategory": "Expenses"
    },
    {
        "model_name": Membership,
        "Category": "Settings",
        "SubCategory": "Membership"
    },
    {
        "model_name": BedBookingPackage,
        "Category": "Settings",
        "SubCategory": "Bed Booking Package"
    },
    {
        "model_name": MedicineBookingPackage,
        "Category": "Settings",
        "SubCategory": "Medicine Booking Package"
    },
    {
        "model_name": Patients,
        "Category": "Patient",
        "SubCategory": "Profile"
    },
    {
        "model_name": PatientMembership,
        "Category": "Patient",
        "SubCategory": "Membership"
    },
    {
        "model_name": PatientRegistration,
        "Category": "Patient",
        "SubCategory": "Registration"
    },
    {
        "model_name": Appointment,
        "Category": "Calendar",
        "SubCategory": "Appointment"
    },
    {
        "model_name": BlockCalendar,
        "Category": "Calendar",
        "SubCategory": "Block Calendar"
    },
    {
        "model_name": PatientInvoices,
        "Category": "Billing",
        "SubCategory": "Invoice"
    },
    {
        "model_name": Reservations,
        "Category": "Billing",
        "SubCategory": "Booking"
    },
    {
        "model_name": PatientPayment,
        "Category": "Billing",
        "SubCategory": "Payment"
    },
    {
        "model_name": ReturnPayment,
        "Category": "Billing",
        "SubCategory": "Return"
    },
    {
        "model_name": PatientVitalSigns,
        "Category": "EMR",
        "SubCategory": "Report Manual"
    },
    {
        "model_name": PatientClinicNotes,
        "Category": "EMR",
        "SubCategory": "Clinical Notes"
    },
    {
        "model_name": PatientProcedure,
        "Category": "EMR",
        "SubCategory": "Treatment Plans/Procedures"
    },
    {
        "model_name": PatientFile,
        "Category": "EMR",
        "SubCategory": "Files"
    },
    {
        "model_name": PatientPrescriptions,
        "Category": "EMR",
        "SubCategory": "Prescriptions"
    },
    {
        "model_name": InventoryItem,
        "Category": "Inventory",
        "SubCategory": "Item"
    },
    {
        "model_name": Meeting,
        "Category": "Meeting",
        "SubCategory": "Meeting"
    },
    {
        "model_name": UserTasks,
        "Category": "Task Track",
        "SubCategory": "Task"
    },
    {
        "model_name": TaskTemplates,
        "Category": "Task Track",
        "SubCategory": "Recurring Task"
    },
    {
        "model_name": TaskComments,
        "Category": "Task Track",
        "SubCategory": "Task Comment"
    }
]
