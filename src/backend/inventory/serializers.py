from datetime import date

from ..base.serializers import ModelSerializer, serializers
from ..inventory.models import Manufacturer, PracticeInventory, InventoryItem, ItemTypeStock, StockEntryItem, \
    Supplier, InventoryCsvReports, HsnCode
from ..mlm.serializers import ProductMarginSerializer
from django.conf import settings
from django.db.models import Sum


class ManufacturerSerializer(ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'


class HsnCodeSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()
    state_taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = HsnCode
        fields = '__all__'

    def get_taxes_data(self, obj):
        from ..practice.serializers import TaxesSerializer
        return TaxesSerializer(obj.taxes.all(), many=True).data

    def get_state_taxes_data(self, obj):
        from ..practice.serializers import TaxesSerializer
        return TaxesSerializer(obj.state_taxes.all(), many=True).data


class PracticeInventorySerializer(ModelSerializer):
    class Meta:
        model = PracticeInventory
        fields = '__all__'


class InventoryItemNameSerializer(ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ('id', 'name')


class InventoryItemInvoiceSerializer(ModelSerializer):
    hsn_data = serializers.SerializerMethodField()
    item_type_stock = serializers.SerializerMethodField()
    strength_type_data = serializers.SerializerMethodField()
    drug_type_data = serializers.SerializerMethodField()
    manufacturer_data = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    margin_data = serializers.SerializerMethodField()
    drug_type_extra = serializers.CharField(required=False)
    unit_type_extra = serializers.CharField(required=False)
    manufacturer_extra = serializers.CharField(required=False)

    class Meta:
        model = InventoryItem
        fields = '__all__'

    def get_total_quantity(self, obj):
        data = 0
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today()).aggregate(
                total_qty=Sum('quantity'))
            data = stock_items["total_qty"]
        return int(data) if data else 0

    def get_item_type_stock(self, obj):
        data = {}
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today())
            item_stocks = ItemTypeStockSerializer(stock_items, many=True).data
            batch_numbers = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today()).values(
                'batch_number', 'expiry_date').distinct()
            data.update({"item_stock": item_stocks, "batch_number": batch_numbers})
        return data

    def get_drug_type_data(self, obj):
        from ..practice.serializers import DrugTypeSerializer
        data = DrugTypeSerializer(obj.drug_type).data
        return data

    def get_strength_type_data(self, obj):
        from ..practice.serializers import DrugUnitSerializer
        data = DrugUnitSerializer(obj.drug_type).data
        return data

    def get_manufacturer_data(self, obj):
        return ManufacturerSerializer(obj.manufacturer).data if obj.manufacturer else None

    def get_hsn_data(self, obj):
        return HsnCodeSerializer(obj.hsn).data if obj.hsn else None

    def get_margin_data(self, obj):
        return ProductMarginSerializer(obj.margin).data if obj.margin else None


class InventoryItemSerializer(ModelSerializer):
    hsn_data = serializers.SerializerMethodField()
    item_type_stock = serializers.SerializerMethodField()
    expired_item_stock = serializers.SerializerMethodField()
    strength_type_data = serializers.SerializerMethodField()
    drug_type_data = serializers.SerializerMethodField()
    manufacturer_data = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    margin_data = serializers.SerializerMethodField()
    drug_type_extra = serializers.CharField(required=False)
    unit_type_extra = serializers.CharField(required=False)
    manufacturer_extra = serializers.CharField(required=False)

    class Meta:
        model = InventoryItem
        fields = '__all__'

    def create(self, validated_data):
        from ..practice.models import DrugType, DrugUnit
        extra_type = validated_data.pop('drug_type_extra', None)
        unit_type_extra = validated_data.pop('unit_type_extra', None)
        manufacturer_extra = validated_data.pop('manufacturer_extra', None)
        practice = validated_data.get('practice', None)
        instance = None
        if practice:
            instance = practice
        update_object = InventoryItem.objects.create(**validated_data)
        if extra_type:
            drug_type_obj, flag = DrugType.objects.get_or_create(practice=instance, name=extra_type)
            update_object.drug_type = drug_type_obj
            update_object.save()
        if unit_type_extra:
            unit_type_obj, flag = DrugUnit.objects.get_or_create(practice=instance, name=unit_type_extra)
            update_object.stength_unit = unit_type_obj
            update_object.save()
        if manufacturer_extra:
            manufacturer_obj, flag = Manufacturer.objects.get_or_create(practice=instance, name=manufacturer_extra)
            update_object.manufacturer = manufacturer_obj
            update_object.save()
        return update_object

    def update(self, instance, validated_data):
        from ..practice.models import DrugType, DrugUnit
        extra_type = validated_data.pop('drug_type_extra', None)
        unit_type_extra = validated_data.pop('unit_type_extra', None)
        manufacturer_extra = validated_data.pop('manufacturer_extra', None)
        practice = validated_data.get('practice', None)
        InventoryItem.objects.filter(id=instance.pk).update(**validated_data)
        update_object = InventoryItem.objects.get(id=instance.pk)
        if practice:
            practice_instance = practice
        if extra_type:
            drug_type_obj, flag = DrugType.objects.get_or_create(practice=practice_instance, name=extra_type)
            update_object.drug_type = drug_type_obj
            update_object.save()
        if unit_type_extra:
            unit_type_obj, flag = DrugUnit.objects.get_or_create(practice=practice_instance, name=unit_type_extra)
            update_object.stength_unit = unit_type_obj
            update_object.save()
        if manufacturer_extra:
            manufacturer_obj, flag = Manufacturer.objects.get_or_create(practice=practice_instance,
                                                                        name=manufacturer_extra)
            update_object.manufacturer = manufacturer_obj
            update_object.save()
        return update_object

    def get_total_quantity(self, obj):
        data = 0
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today()).aggregate(
                total_qty=Sum('quantity'))
            data = stock_items["total_qty"]
        return int(data) if data else 0

    def get_hsn_data(self, obj):
        return HsnCodeSerializer(obj.hsn).data if obj.hsn else None

    def get_item_type_stock(self, obj):
        data = {}
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today(),
                                                       quantity__gt=0)
            item_stocks = ItemTypeStockSerializer(stock_items, many=True).data
            batch_numbers = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__gt=date.today(),
                                                         quantity__gt=0).values('batch_number',
                                                                                'expiry_date').distinct()
            data.update({"item_stock": item_stocks, "batch_number": batch_numbers})
        return data

    def get_expired_item_stock(self, obj):
        data = {}
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__lte=date.today(),
                                                       quantity__gt=0)
            item_stocks = ItemTypeStockSerializer(stock_items, many=True).data
            batch_numbers = ItemTypeStock.objects.filter(inventory_item=obj, expiry_date__lte=date.today(),
                                                         quantity__gt=0).values('batch_number',
                                                                                'expiry_date', 'quantity').distinct()
            data.update({"item_stock": item_stocks, "batch_number": batch_numbers})
        return data

    def get_drug_type_data(self, obj):
        from ..practice.serializers import DrugTypeSerializer
        data = DrugTypeSerializer(obj.drug_type).data
        return data

    def get_strength_type_data(self, obj):
        from ..practice.serializers import DrugUnitSerializer
        data = DrugUnitSerializer(obj.drug_type).data
        return data

    def get_manufacturer_data(self, obj):
        data = ManufacturerSerializer(obj.manufacturer).data
        return data

    def get_margin_data(self, obj):
        return ProductMarginSerializer(obj.margin).data if obj.margin else None


class InventoryItemDetailSerializer(ModelSerializer):
    from ..practice.serializers import VendorSerializer
    inventory = PracticeInventorySerializer(required=False)
    manufacturer = ManufacturerSerializer(required=False)
    vendor = VendorSerializer(required=False)
    hsn_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = (
            'id', 'inventory', 'name', 'code', 'manufacturer', 'vendor', 're_order_level', 'item_type', 'hsn_data',
            'is_active')

    def get_hsn_data(self, obj):
        return HsnCodeSerializer(obj.hsn).data if obj.hsn else None


class ItemTypeStockSerializer(ModelSerializer):
    item = serializers.SerializerMethodField(required=False)

    class Meta:
        model = ItemTypeStock
        fields = '__all__'

    def get_item(self, obj):
        return InventoryItemDetailSerializer(obj.inventory_item).data if obj.inventory_item else None


class InventoryItemDataSerializer(ModelSerializer):
    from ..practice.serializers import VendorSerializer
    inventory = PracticeInventorySerializer(required=False)
    manufacturer = ManufacturerSerializer(required=False)
    vendor = VendorSerializer(required=False)
    item_type_stock = serializers.SerializerMethodField()
    hsn_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = (
            'id', 'inventory', 'name', 'code', 'manufacturer', 'vendor', 're_order_level', 'item_type',
            'item_type_stock', 'is_active', 'retail_without_tax', 'retail_with_tax', 'hsn_data')

    def get_item_type_stock(self, obj):
        data = {}
        if ItemTypeStock.objects.filter(inventory_item=obj).exists():
            stock_items = ItemTypeStock.objects.filter(inventory_item=obj)
            item_stocks = ItemTypeStockSerializer(stock_items, many=True).data
            batch_numbers = ItemTypeStock.objects.filter(inventory_item=obj).values('batch_number').distinct()
            data.update({"item_stock": item_stocks, "batch_number": batch_numbers})
        return data

    def get_hsn_data(self, obj):
        return HsnCodeSerializer(obj.hsn).data if obj.hsn else None


class SupplierSerializer(ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class InventoryCsvReportsSerializer(ModelSerializer):
    report_csv = serializers.SerializerMethodField()
    report_pdf = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCsvReports
        fields = '__all__'

    def get_report_csv(self, obj):
        return settings.MEDIA_URL + obj.report_csv.name if obj.report_csv else None

    def get_report_pdf(self, obj):
        return settings.MEDIA_URL + obj.report_pdf.name if obj.report_pdf else None


class StockEntryItemDistinctSerializer(ModelSerializer):
    supplier_data = serializers.SerializerMethodField()

    class Meta:
        model = StockEntryItem
        fields = ('id', 'supplier', 'bill_number', 'supplier_data', 'remarks', 'date', 'created_at', 'modified_at')

    def get_supplier_data(self, obj):
        return SupplierSerializer(obj.supplier).data if obj.supplier else None


class StockEntryItemSerializer(ModelSerializer):
    supplier_name = serializers.CharField(required=False)
    supplier_data = serializers.SerializerMethodField()
    inventory_item_data = serializers.SerializerMethodField()

    class Meta:
        model = StockEntryItem
        fields = '__all__'

    def create(self, validated_data):
        supplier_name = validated_data.pop("supplier_name", None)
        if supplier_name:
            practice = validated_data["inventory_item"].practice if validated_data["inventory_item"] else None
            supplier = Supplier.objects.create(name=supplier_name, practice=practice)
            validated_data["supplier"] = supplier
        stocking_entry_obj = StockEntryItem.objects.create(**validated_data)
        # if stocking_entry_obj.quantity:
        # this means we have to according tyoe consume or add to it
        if stocking_entry_obj.item_add_type == 'ADD':
            inventory_item = stocking_entry_obj.inventory_item
            if ItemTypeStock.objects.filter(inventory_item=inventory_item,
                                            batch_number=stocking_entry_obj.batch_number).exists():
                stock_item = ItemTypeStock.objects.filter(inventory_item=inventory_item,
                                                          batch_number=stocking_entry_obj.batch_number)[0]
            else:
                stock_item = ItemTypeStock.objects.create(inventory_item=inventory_item,
                                                          unit_cost=stocking_entry_obj.unit_cost,
                                                          batch_number=stocking_entry_obj.batch_number,
                                                          expiry_date=stocking_entry_obj.expiry_date, quantity=0)
            stock_item.quantity = stock_item.quantity + stocking_entry_obj.quantity
            stock_item.save()

        if stocking_entry_obj.item_add_type == 'CONSUME':
            inventory_item = stocking_entry_obj.inventory_item
            if ItemTypeStock.objects.filter(inventory_item=inventory_item,
                                            batch_number=stocking_entry_obj.batch_number).exists():
                stock_item = ItemTypeStock.objects.filter(inventory_item=inventory_item,
                                                          batch_number=stocking_entry_obj.batch_number)[0]
            else:
                stock_item = ItemTypeStock.objects.create(inventory_item=inventory_item,
                                                          unit_cost=stocking_entry_obj.unit_cost,
                                                          batch_number=stocking_entry_obj.batch_number,
                                                          expiry_date=stocking_entry_obj.expiry_date, quantity=0)
            stock_item.quantity = stock_item.quantity - stocking_entry_obj.quantity
            stock_item.save()
        return stocking_entry_obj

    def get_supplier_data(self, obj):
        return SupplierSerializer(obj.supplier).data if obj.supplier else None

    def get_inventory_item_data(self, obj):
        return InventoryItemDetailSerializer(obj.inventory_item).data if obj.inventory_item else None
