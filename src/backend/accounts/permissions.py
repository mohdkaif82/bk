from ..base.api.permissions import (AllowAny, IsAuthenticated, PermissionComponent, ResourcePermission)


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class UserPermissions(ResourcePermission):
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsTheSameUser()
    create_perms = IsAuthenticated()
    update_perms = IsTheSameUser()
    partial_update_perms = IsTheSameUser()
    destroy_perms = IsTheSameUser()
    list_perms = IsAuthenticated()
    login_perms = AllowAny()
    logout_perms = IsAuthenticated()
    passwordchange_perms = IsAuthenticated()
    register_perms = IsAuthenticated()
    registered_list_perms = IsAuthenticated()
    approve_perms = IsAuthenticated()
    permission_group_perms = IsAuthenticated()
    staff_reset_mail_perms = IsAuthenticated()
    reset_password_perms = IsAuthenticated()
    user_clone_perms = IsAuthenticated()
    sms_status_update_perms = IsAuthenticated()
    all_permissions_perms = IsAuthenticated()
    task_login_perms = IsAuthenticated()
    config_perms = AllowAny()
    reports_mail_perms = IsAuthenticated()
    referer_perms = IsAuthenticated()
    generate_referer_perms = IsAuthenticated()


class PatientLoginPermissions(ResourcePermission):
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsTheSameUser()
    create_perms = IsAuthenticated()
    update_perms = IsTheSameUser()
    partial_update_perms = IsTheSameUser()
    destroy_perms = IsTheSameUser()
    send_otp_perms = AllowAny()
    verify_otp_perms = AllowAny()
    resend_otp_perms = AllowAny()
    registration_otp_perms = AllowAny()
    registration_verify_perms = AllowAny()
    resend_registration_perms = AllowAny()
    switch_perms = IsAuthenticated()


class StaffLoginPermissions(ResourcePermission):
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsTheSameUser()
    create_perms = IsAuthenticated()
    update_perms = IsTheSameUser()
    partial_update_perms = IsTheSameUser()
    destroy_perms = IsTheSameUser()
    send_otp_perms = AllowAny()
    verify_otp_perms = AllowAny()
    resend_otp_perms = AllowAny()
    switch_perms = IsAuthenticated()
