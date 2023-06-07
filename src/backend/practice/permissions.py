from ..base.api.permissions import (IsAuthenticated, PermissionComponent, ResourcePermission,
                                          IsGetMethodOrAuthenticated, AllowAny)


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class PracticePermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsGetMethodOrAuthenticated()
    calender_settings_perms = IsAuthenticated()
    appointment_category_perms = IsAuthenticated()
    practice_staff_perms = IsAuthenticated()
    update_staff_perms = IsAuthenticated()
    procedure_category_perms = IsAuthenticated()
    taxes_perms = IsAuthenticated()
    payment_modes_perms = IsAuthenticated()
    payment_config_perms = IsAuthenticated()
    offers_perms = IsAuthenticated()
    referer_perms = IsAuthenticated()
    complaints_perms = IsAuthenticated()
    observations_perms = IsAuthenticated()
    diagnoses_perms = IsAuthenticated()
    investigations_perms = IsAuthenticated()
    treatmentnotes_perms = IsAuthenticated()
    filetags_perms = IsAuthenticated()
    data_list_perms = IsAuthenticated()
    communications_perms = IsAuthenticated()
    email_communications_perms = IsAuthenticated()
    labtest_perms = IsAuthenticated()
    labpanel_perms = IsAuthenticated()
    drugcatalog_perms = IsAuthenticated()
    drugtype_perms = IsAuthenticated()
    drugunit_perms = IsAuthenticated()
    expense_type_perms = IsAuthenticated()
    extra_data_perms = IsAuthenticated()
    appointment_report_perms = IsAuthenticated()
    emr_report_perms = IsAuthenticated()
    payments_report_perms = IsAuthenticated()
    invoice_report_perms = IsAuthenticated()
    expense_report_perms = IsAuthenticated()
    fianancial_report_perms = IsAuthenticated()
    prescription_template_perms = IsAuthenticated()
    patients_report_perms = IsAuthenticated()
    delete_clinic_perms = IsAuthenticated()
    vendor_perms = IsAuthenticated()
    practice_print_settings_perms = IsAuthenticated()
    room_types_perms = IsAuthenticated()
    medicine_packages_perms = IsGetMethodOrAuthenticated()
    bed_packages_perms = IsGetMethodOrAuthenticated()
    doctor_timing_perms = IsAuthenticated()
    all_print_settings_perms = IsAuthenticated()
    membership_perms = IsAuthenticated()
    registration_perms = IsAuthenticated()
    vital_sign_perms = IsAuthenticated()
    seat_availability_perms = IsGetMethodOrAuthenticated()
    seat_booking_perms = AllowAny()
    seat_booking_report_perms = IsAuthenticated()
    accept_payments_perms = IsAuthenticated()
    other_diseases_perms = IsGetMethodOrAuthenticated()
    medication_perms = IsAuthenticated()
    payment_perms = IsAuthenticated()
    booking_pdf_perms = IsGetMethodOrAuthenticated()
    user_permissions_perms = IsAuthenticated()


class PracticeStaffPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    roles_perms = IsAuthenticated()
    practice_list_perms = IsAuthenticated()
    task_login_perms = IsAuthenticated()
    employees_perms = IsAuthenticated()
    advisors_perms = IsAuthenticated()
    permission_group_perms = IsAuthenticated()
    assign_group_perms = IsAuthenticated()


class VendorPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()


class ExpensesPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    report_perms = IsAuthenticated()


class ActivityLogPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    category_perms = IsAuthenticated()
    subcategory_perms = IsAuthenticated()


class DrugTypePermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()


class DrugUnitPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()


class PracticeUserPermissionsPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    permissions_perms = IsAuthenticated()
    bulk_perms = IsAuthenticated()
    Informational_perms = IsAuthenticated()


class PracticePrintSettingsPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
