import datetime

# Create your models here.
from ..base.models import TimeStampedModel
from ..base.validators.form_validations import file_extension_validator
from ..mlm.models import ProductMargin
from ..practice.models import Taxes, Practice, Vendor, DrugType, DrugUnit
from django.db import models


class Manufacturer(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=1024, blank=True, null=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PracticeInventory(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class HsnCode(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    code = models.CharField(max_length=524, blank=True, null=True)
    taxes = models.ManyToManyField(Taxes, related_name="inventory_normal_tax", blank=True)
    state_taxes = models.ManyToManyField(Taxes, related_name="inventory_other_state_tax", blank=True)
    is_active = models.BooleanField(default=True)


class InventoryItem(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=524, blank=True, null=True)
    code = models.CharField(max_length=524, blank=True, null=True)
    hsn = models.ForeignKey(HsnCode, blank=True, null=True, on_delete=models.PROTECT)
    manufacturer = models.ForeignKey(Manufacturer, blank=True, null=True, on_delete=models.PROTECT)
    vendor = models.ForeignKey(Vendor, blank=True, null=True, on_delete=models.PROTECT)
    re_order_level = models.IntegerField(blank=True, null=True)
    item_type = models.CharField(max_length=524, blank=True, null=True)
    package_details = models.CharField(max_length=1024, blank=True, null=True)
    perscribe_this = models.BooleanField(default=True)
    margin = models.ForeignKey(ProductMargin, blank=True, null=True, on_delete=models.PROTECT)
    mlm_applicable = models.BooleanField(default=False)
    stocking_unit = models.CharField(max_length=524, blank=True, null=True)
    instructions = models.CharField(max_length=524, blank=True, null=True)
    point_value = models.FloatField(blank=True, null=True)
    business_value = models.FloatField(blank=True, null=True)
    strength = models.FloatField(blank=True, null=True)
    stength_unit = models.ForeignKey(DrugUnit, blank=True, null=True, on_delete=models.PROTECT)
    drug_type = models.ForeignKey(DrugType, blank=True, null=True, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    maintain_inventory = models.BooleanField(default=True)
    retail_without_tax = models.FloatField(blank=True, null=True)
    retail_with_tax = models.FloatField(blank=True, null=True)


class ItemTypeStock(TimeStampedModel):
    batch_number = models.CharField(max_length=1024, blank=True, null=True)
    item_type = models.CharField(max_length=524, blank=True, null=True)
    inventory_item = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    quantity = models.FloatField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    unit_cost = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Supplier(TimeStampedModel):
    practice = models.ForeignKey(Practice, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1024, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class StockEntryItem(TimeStampedModel):
    batch_number = models.CharField(max_length=1024, blank=True, null=True)
    item_add_type = models.CharField(max_length=524, blank=True, null=True)
    bill_number = models.CharField(max_length=524, blank=True, null=True)
    inventory_item = models.ForeignKey(InventoryItem, blank=True, null=True, on_delete=models.PROTECT)
    quantity = models.FloatField(blank=True, null=True)
    unit_cost = models.FloatField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    total_cost = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_processed = models.BooleanField(default=True)
    supplier = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.PROTECT)
    date = models.DateField(blank=True, null=True, default=datetime.date.today)
    type_of_consumption = models.CharField(max_length=50, blank=True, null=True, default="SALES")
    bill_file = models.CharField(max_length=524, blank=True, null=True)
    remarks = models.CharField(max_length=524, blank=True, null=True)
    read = models.BooleanField(default=True)


class InventoryCsvReports(TimeStampedModel):
    inventory = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    report_csv = models.FileField(upload_to="inventory-csv/%Y/%m/%d", max_length=80, blank=True, null=True,
                                  validators=[file_extension_validator])
    report_pdf = models.FileField(upload_to="inventory-csv/%Y/%m/%d", max_length=80, blank=True, null=True,
                                  validators=[file_extension_validator])
