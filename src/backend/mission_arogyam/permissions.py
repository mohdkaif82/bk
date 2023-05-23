from ..base.api.permissions import (PermissionComponent, ResourcePermission, IsAuthenticated, AllowAny)


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class PostPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()
    slug_perms = AllowAny()
    comments_perms = AllowAny()
    ratings_perms = AllowAny()


class VideoFilePermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()


class DiseasePermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()
    slug_perms = AllowAny()


class EventsPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()
    slug_perms = AllowAny()


class ContactUsPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    create_perms = AllowAny()
    retrieve_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()


class PageSEOPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    create_perms = IsAuthenticated()
    retrieve_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()


class SliderPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()


class CommentPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = AllowAny()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()


class RatingPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = AllowAny()
    update_perms = AllowAny()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = AllowAny()
    create_with_ip_perms = AllowAny()


class ContactUsFormPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = AllowAny()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()


class SuggestionBoxPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    create_perms = AllowAny()
    retrieve_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
