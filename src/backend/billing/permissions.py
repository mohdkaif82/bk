from ..base.api.permissions import PermissionComponent, ResourcePermission, IsAuthenticated


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class BillingPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    invoice_reports_perms = IsAuthenticated()
    return_reports_perms = IsAuthenticated()
    payment_reports_perms = IsAuthenticated()
    update_id_perms = IsAuthenticated()
    promo_code_sms_perms = IsAuthenticated()
    export_perms = IsAuthenticated()
    get_pdf_perms = IsAuthenticated()
    amount_due_perms = IsAuthenticated()
    get_payments_perms = IsAuthenticated()
    bulk_payments_perms = IsAuthenticated()
    ledger_sum_perms = IsAuthenticated()
    top_advisor_perms = IsAuthenticated()
    promo_value_perms = IsAuthenticated()
