from django.contrib import admin

# Register your models here.
from ..inventory.models import Manufacturer, PracticeInventory, InventoryItem, ItemTypeStock, StockEntryItem

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
	pass

@admin.register(PracticeInventory)
class PracticeInventoryAdmin(admin.ModelAdmin):
	pass

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
	pass

@admin.register(ItemTypeStock)
class ItemTypeStockAdmin(admin.ModelAdmin):
	pass

@admin.register(StockEntryItem)
class StockEntryItemAdmin(admin.ModelAdmin):
	pass