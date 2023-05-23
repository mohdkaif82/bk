from ..base.api.permissions import (PermissionComponent, ResourcePermission, IsAuthenticated)


class IsTheSameUser(PermissionComponent):
    def has_permission(self, request, view):
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj=None):
        return request.user.is_authenticated() and request.user.pk == obj.pk


class InventoryPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    add_bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()


class ManufacturerPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    add_bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()


class PracticeInventoryPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    add_bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()
    item_stock_perms = IsAuthenticated()


class InventoryItemPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    add_bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()
    practice_item_stock_perms = IsAuthenticated()
    export_perms = IsAuthenticated()
    products_perms = IsAuthenticated()
    inventory_retail_perms = IsAuthenticated()
    inventory_report_perms = IsAuthenticated()
    inventory_total_perms = IsAuthenticated()
    match_inventory_perms = IsAuthenticated()
    hsn_code_perms = IsAuthenticated()


class ItemTypeStockPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    add_bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()
    find_item_perms = IsAuthenticated()


class StockEntryItemPermissions(ResourcePermission):
    metadata_perms = IsAuthenticated()
    enough_perms = IsAuthenticated()
    global_perms = None
    retrieve_perms = IsAuthenticated()
    create_perms = IsAuthenticated()
    update_perms = IsAuthenticated()
    partial_update_perms = IsAuthenticated()
    destroy_perms = IsAuthenticated()
    list_perms = IsAuthenticated()
    bulk_perms = IsAuthenticated()
    move_inventory_item_perms = IsAuthenticated()
    practice_supplier_perms = IsAuthenticated()
    bills_suppliers_perms = IsAuthenticated()
