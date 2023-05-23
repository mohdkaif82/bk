# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import datetime
import operator
import os
from datetime import timedelta

import pandas as pd
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..constants import CONST_GLOBAL_PRACTICE
from .models import Manufacturer, PracticeInventory, InventoryItem, ItemTypeStock, StockEntryItem, \
    Supplier, InventoryCsvReports, HsnCode
from .permissions import ManufacturerPermissions, PracticeInventoryPermissions, \
    InventoryItemPermissions, ItemTypeStockPermissions, StockEntryItemPermissions
from .serializers import ManufacturerSerializer, PracticeInventorySerializer, InventoryItemSerializer, \
    ItemTypeStockSerializer, StockEntryItemSerializer, InventoryItemDataSerializer, SupplierSerializer, \
    StockEntryItemDistinctSerializer, InventoryCsvReportsSerializer, InventoryItemNameSerializer, HsnCodeSerializer
from ..patients.models import InventoryCatalogInvoice
from ..patients.services import create_update_record
from ..practice.models import Practice
from ..practice.serializers import PracticeBasicSerializer
from ..practice.services import dict_to_mail
from ..utils.pdf_document import html_to_pdf_convert
from django.conf import settings
from django.core.files.base import File
from django.db.models import F, Sum
from django.db.models.functions import TruncMonth as Month, TruncYear as Year, TruncDay as Day
from django.template import Template, Context
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class ManufacturerViewSet(ModelViewSet):
    serializer_class = ManufacturerSerializer
    queryset = Manufacturer.objects.filter(is_active=True)
    permission_classes = (ManufacturerPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ManufacturerViewSet, self).get_queryset()
        return queryset


class PracticeInventoryViewSet(ModelViewSet):
    serializer_class = PracticeInventorySerializer
    queryset = PracticeInventory.objects.filter(is_active=True)
    permission_classes = (PracticeInventoryPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(PracticeInventoryViewSet, self).get_queryset()
        return queryset

    @action(methods=['GET'], detail=True)
    def item_stock(self):
        instance = self.get_object()
        return response.Ok(
            InventoryItemDataSerializer(InventoryItem.objects.filter(inventory=instance), many=True).data)


class InventoryItemViewSet(ModelViewSet):
    serializer_class = InventoryItemSerializer
    queryset = InventoryItem.objects.filter(is_active=True)
    permission_classes = (InventoryItemPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        practice = self.request.query_params.get('practice', None)
        item_type = self.request.query_params.get('item_type', None)
        filter_type = self.request.query_params.get('filter_type', None)
        item_name = self.request.query_params.get('item_name', None)
        item_code = self.request.query_params.get('code', None)
        margin = self.request.query_params.get('margin', None)
        mlm_applicable = self.request.query_params.get('mlm_applicable', None)
        item_name_equals = self.request.query_params.get('item_name_equals', None)
        maintain_inventory = self.request.query_params.get('maintain_inventory', None)
        sort = self.request.query_params.get('sort', None)
        queryset = super(InventoryItemViewSet, self).get_queryset()
        if maintain_inventory:
            inventory = True if maintain_inventory == "true" else False
            queryset = queryset.filter(maintain_inventory=inventory)
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        if practice:
            queryset = queryset.filter(practice__id=practice)
        if item_name:
            queryset = queryset.filter(name__icontains=item_name)
        if item_name_equals:
            queryset = queryset.filter(name=item_name_equals)
        if item_code:
            queryset = queryset.filter(hsn__code__icontains=item_code)
        if margin:
            queryset = queryset.filter(margin=margin)
        if mlm_applicable:
            mlm_applicable = True if mlm_applicable == "true" else False
            queryset = queryset.filter(mlm_applicable=mlm_applicable)
        if filter_type and filter_type == "Low":
            for obj in queryset:
                if ItemTypeStock.objects.filter(inventory_item=obj).exists():
                    stock_items = ItemTypeStock.objects.filter(inventory_item=obj,
                                                               expiry_date__gt=datetime.date.today()).aggregate(
                        total_qty=Sum('quantity'))
                    qty = stock_items["total_qty"]
                    if not obj.re_order_level:
                        queryset = queryset.exclude(id=obj.pk)
                    elif qty and int(qty) > obj.re_order_level:
                        queryset = queryset.exclude(id=obj.pk)
        elif filter_type and filter_type == "Expired":
            for obj in queryset:
                if ItemTypeStock.objects.filter(inventory_item=obj).exists():
                    stock_items = ItemTypeStock.objects.filter(inventory_item=obj, quantity__gt=0,
                                                               expiry_date__lte=datetime.date.today()).count()
                    if stock_items == 0:
                        queryset = queryset.exclude(id=obj.pk)
                else:
                    queryset = queryset.exclude(id=obj.pk)
        if sort:
            on = self.request.query_params.get("on", None)
            if on == 'name' and sort == 'asc':
                queryset = queryset.order_by("name")
            elif on == 'name' and sort == 'desc':
                queryset = queryset.order_by("-name")
        queryset = queryset.prefetch_related('drug_type')
        return queryset

    def list(self, request):
        sort = self.request.query_params.get('sort', None)
        queryset = super(InventoryItemViewSet, self).list(request)
        if sort:
            on = self.request.query_params.get("on", None)
            if on == 'total_quantity' and sort == 'asc':
                queryset.data['results'] = sorted(queryset.data['results'], key=operator.itemgetter(on))
            elif on == 'total_quantity' and sort == 'desc':
                queryset.data['results'] = sorted(queryset.data['results'], key=operator.itemgetter(on), reverse=True)
        return queryset

    @action(methods=['GET'], detail=False)
    def inventory_total(self, request):
        practice = request.query_params.get('practice', None)
        queryset = InventoryItem.objects.filter(is_active=True, maintain_inventory=True)
        if practice:
            queryset = queryset.filter(practice__id=practice)
        total_price = 0
        for obj in queryset:
            if ItemTypeStock.objects.filter(inventory_item=obj).exists():
                stock_price = ItemTypeStock.objects.filter(inventory_item=obj,
                                                           expiry_date__gt=datetime.date.today()).annotate(
                    total=F('unit_cost') * F('quantity')).values('total')
                for price in stock_price:
                    total_price += float(price["total"]) if "total" in price and price["total"] else 0
        return response.Ok({"total_price": total_price})

    @action(methods=['GET', 'POST'], detail=False)
    def hsn_code(self, request):
        if request.method == "GET":
            code = request.query_params.get("code", None)
            practice = request.query_params.get("practice", None)
            queryset = HsnCode.objects.filter(is_active=True)
            if practice:
                queryset = queryset.filter(practice=practice)
            if code:
                queryset = queryset.filter(code=code)
            return response.Ok(HsnCodeSerializer(queryset, many=True).data)
        else:
            return response.Ok(create_update_record(request, HsnCodeSerializer, HsnCode))

    @action(methods=['GET'], detail=False)
    def match_inventory(self, request):
        practice = request.query_params.get('practice', None)
        mail_to = request.query_params.get('mail_to', None)
        if practice:
            result = []
            practice_name = Practice.objects.get(id=practice).name
            all_practices = Practice.objects.filter(is_active=True).exclude(id=practice)
            practice_ids = all_practices.values_list('id')
            queryset = InventoryItem.objects.filter(is_active=True, maintain_inventory=True,
                                                    practice=practice).order_by('name')
            for item in queryset:
                all_items = InventoryItem.objects.filter(name=item.name, practice__in=practice_ids,
                                                         is_active=True).values_list('practice')
                if not len(all_items) == len(all_practices):
                    detail = {"id": item.id, "name": item.name}
                    for practice_id in practice_ids:
                        if practice_id in list(all_items):
                            detail["practice_" + str(practice_id[0])] = True
                        else:
                            detail["practice_" + str(practice_id[0])] = False
                    result.append(detail)
            if mail_to:
                ready_data = []
                for item in result:
                    detail = {"Item": item.get("name", None)}
                    for practice_obj in all_practices:
                        detail[practice_obj.name] = "Exists" if item[
                            "practice_" + str(practice_obj.id)] else "Not Exists"
                    ready_data.append(detail)
                subject = "Mismanaged Inventory on all practices"
                body = "As Requested on ERP System, Please find the report in the attachment.<br><br>Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Mismanaged_Inventory_Report", mail_to, subject,
                                          body)
                res = {"detail": msg, "error": error}
                if "error" in res and res["error"]:
                    return response.BadRequest(res)
                return response.Ok(res)
            return response.Ok(
                {"practices": PracticeBasicSerializer(all_practices, many=True).data, "item_detail": result})
        else:
            return response.BadRequest({"detail": "Please select a practice"})

    @action(methods=['GET'], detail=False)
    def export(self, request):
        practice = request.query_params.get('practice', None)
        item_type = request.query_params.get('item_type', None)
        filter_type = request.query_params.get('filter_type', None)
        item_name = request.query_params.get('item_name', None)
        item_code = request.query_params.get('code', None)
        item_name_equals = request.query_params.get('item_name_equals', None)
        mlm_applicable = request.query_params.get('mlm_applicable', None)
        maintain_inventory = request.query_params.get('maintain_inventory', None)
        sort = request.query_params.get('sort', None)
        queryset = InventoryItem.objects.filter(is_active=True)
        if maintain_inventory:
            inventory = True if maintain_inventory == "true" else False
            queryset = queryset.filter(maintain_inventory=inventory)
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        if practice:
            queryset = queryset.filter(practice__id=practice)
        if item_name:
            queryset = queryset.filter(name__icontains=item_name)
        if item_name_equals:
            queryset = queryset.filter(name=item_name_equals)
        if item_code:
            queryset = queryset.filter(hsn__code__icontains=item_code)
        if mlm_applicable:
            mlm_applicable = True if mlm_applicable == "true" else False
            queryset = queryset.filter(mlm_applicable=mlm_applicable)
        if filter_type and filter_type == "Low":
            for obj in queryset:
                if ItemTypeStock.objects.filter(inventory_item=obj).exists():
                    stock_items = ItemTypeStock.objects.filter(inventory_item=obj,
                                                               expiry_date__gt=datetime.date.today()).aggregate(
                        total_qty=Sum('quantity'))
                    qty = stock_items["total_qty"]
                    if not obj.re_order_level:
                        queryset = queryset.exclude(id=obj.pk)
                    elif qty and int(qty) > obj.re_order_level:
                        queryset = queryset.exclude(id=obj.pk)
        elif filter_type and filter_type == "Expired":
            for obj in queryset:
                if ItemTypeStock.objects.filter(inventory_item=obj).exists():
                    stock_items = ItemTypeStock.objects.filter(inventory_item=obj, quantity__gt=0,
                                                               expiry_date__lte=datetime.date.today()).count()
                    if stock_items == 0:
                        queryset = queryset.exclude(id=obj.pk)
                else:
                    queryset = queryset.exclude(id=obj.pk)
        if sort:
            on = self.request.query_params.get("on", None)
            if on == 'name' and sort == 'asc':
                queryset = queryset.order_by("name")
            elif on == 'name' and sort == 'desc':
                queryset = queryset.order_by("-name")
        queryset = queryset.prefetch_related('drug_type')
        inventory = InventoryItemSerializer(queryset, many=True).data
        data = [["Name", "HSN Code", "Inventory Stock", "Expired Stock", "Retail Price (INR)", "Same State Taxes",
                 "Other State Taxes", "MRP", "MLM Margin", "Item Type", "Reorder Level", "Manufacturer", "Stock Cost"]]
        for item in inventory:
            expiry = 0
            taxes = ""
            state_taxes = ""
            cost = 0
            code = item["hsn_data"]["code"] if item.get("hsn_data", None) and \
                                               item.get("hsn_data", None).get("code", None) else "--"
            items = item["item_type_stock"]["item_stock"] if item["item_type_stock"] and item["item_type_stock"][
                "item_stock"] else []
            for batch_item in items:
                if batch_item["expiry_date"] and pd.to_datetime(batch_item["expiry_date"]) <= datetime.datetime.now():
                    expiry += batch_item["quantity"]
                else:
                    qty = batch_item["quantity"] if batch_item["quantity"] else 0
                    unit_cost = batch_item["unit_cost"] if batch_item["unit_cost"] else 0
                    cost += qty * unit_cost
            if item.get("hsn_data", None):
                for tax in item.get("hsn_data", []).get("taxes_data", []):
                    taxes += tax["name"] + "@" + str(tax["tax_value"]) + ", "
                for tax in item.get("hsn_data", []).get("state_taxes_data", []):
                    state_taxes += tax["name"] + "@" + str(tax["tax_value"]) + ", "
                if len(taxes) > 2:
                    taxes = taxes[0:-2]
                if len(state_taxes) > 2:
                    state_taxes = state_taxes[0:-2]
            mlm_name = item["margin_data"]["name"] if item["margin_data"] and "name" in item["margin_data"] and \
                                                      item["margin_data"]["name"] else ""
            item_data = [item["name"], code, item["total_quantity"], expiry, item["retail_without_tax"], taxes,
                         state_taxes, item["retail_with_tax"], mlm_name, item['item_type'], item["re_order_level"],
                         item["manufacturer_data"]["name"], cost]
            data.append(item_data)
        report_name = "Report_Inventory" + "_" + str(datetime.datetime.now())
        report_path = os.path.join(settings.MEDIA_ROOT, report_name + ".csv")
        with open(report_path, 'w') as csv_file:
            csvwriter = csv.writer(csv_file)
            csvwriter.writerows(data)
        csv_data = File(open(report_path, 'rb'))
        pdf_obj, flag = InventoryCsvReports.objects.get_or_create(inventory=report_name)
        pdf_obj.report_csv.save("%s.csv" % report_name, csv_data)
        html_file = report_path[:-3] + 'html'
        df = pd.read_csv(report_path, sep=',', keep_default_na=False)
        df.index += 1
        df.to_html(html_file)
        html_data = Template(
            open(html_file, "r").read() + "<style>.dataframe {text-align:center;padding: 5px 0;}</style>")
        pdf_content = html_to_pdf_convert(html_data, Context({}))
        pdf_obj.report_pdf.save("%s.pdf" % report_name, pdf_content)
        os.remove(html_file)
        os.remove(report_path)
        return response.Ok(InventoryCsvReportsSerializer(pdf_obj).data)

    @action(methods=['GET'], detail=False)
    def practice_item_stock(self, request):
        practice = request.query_params.get('id')
        if practice:
            return response.Ok(
                InventoryItemDataSerializer(InventoryItem.objects.filter(practice__id=practice), many=True).data)
        else:
            return response.Ok(
                InventoryItemDataSerializer(InventoryItem.objects.filter(is_active=True), many=True).data)

    @action(methods=['GET'], detail=False)
    def products(self, request):
        practice = request.query_params.get('practice')
        if practice:
            return response.Ok(
                InventoryItemNameSerializer(InventoryItem.objects.filter(practice=practice, is_active=True),
                                            many=True).data)
        else:
            return response.BadRequest({"detail": "Send practice in query params"})

    @action(methods=['GET'], detail=False)
    def inventory_retail(self, request):
        from ..patients.models import Patients
        groups = request.query_params.get('groups', None)
        practice = request.query_params.get('practice', None)
        products = request.query_params.get('products', None)
        doctors = request.query_params.get('doctors', None)
        manufacturers = request.query_params.get('manufacturers', None)
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        mail_to = request.query_params.get('mail_to', None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        queryset = InventoryCatalogInvoice.objects.filter(is_active=True, patientinvoices__is_cancelled=False,
                                                          inventory__stockentryitem__batch_number=F("batch_number"),
                                                          inventory__stockentryitem__item_add_type="ADD")
        if products:
            product_list = products.split(",")
            queryset = queryset.filter(inventory__in=product_list)
        if practice:
            queryset = queryset.filter(patientinvoices__practice=practice)
        if start and end:
            queryset = queryset.filter(patientinvoices__date__range=[start, end])
        if doctors:
            doctor_list = doctors.split(",")
            queryset = queryset.filter(doctor__in=doctor_list)
        if manufacturers:
            manufacturer_list = manufacturers.split(",")
            queryset = queryset.filter(inventory__manufacturer__in=manufacturer_list)
        if groups:
            group_list = groups.split(",")
            patients = Patients.objects.filter(patient_group__in=group_list).values_list('id', flat=True)
            queryset = queryset.filter(patientinvoices__patient__in=patients)
        queryset = queryset.values('id', 'unit', 'total', 'tax_value', 'patientinvoices__date', 'inventory',
                                   'batch_number').order_by('id', 'patientinvoices__date').distinct('id')
        data = {}
        res = []
        for item in queryset:
            stock = StockEntryItem.objects.filter(batch_number=item['batch_number'], inventory_item=item['inventory'],
                                                  item_add_type="ADD").first()
            if item['patientinvoices__date'] in data:
                data[item['patientinvoices__date']]['total'] += item['total']
                data[item['patientinvoices__date']]['tax'] += item['tax_value']
                data[item['patientinvoices__date']]['cost'] += stock.unit_cost * item['unit'] if stock else 0
            else:
                data[item['patientinvoices__date']] = {'total': item['total'], 'tax': item['tax_value'],
                                                       'cost': stock.unit_cost * item['unit'] if stock else 0}
        for key in data.keys():
            res.append({"date": key, **data[key]})
        if mail_to:
            for index, item in enumerate(res):
                ready_data.append({
                    "S.No. ": index + 1,
                    "date": item['date'],
                    "Sales (INR)": item["total"],
                    "Cost (INR)": item["cost"],
                    "Profit before Tax(INR)": item["total"] - item['cost'],
                    "Tax(INR)": item["tax"],
                    "Profit after Tax(INR)": item["total"] - item['cost'] - item['tax'],
                })
            subject = "Profit Loss Report for " + practice_name + " from " + start + " to " + end
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "Profit_Loss_Report_" + start + "_" + end, mail_to, subject,
                                      body)
            res = {"detail": msg, "error": error}
        if "error" in res and res["error"]:
            return response.BadRequest(res)
        return response.Ok(res)

    @action(methods=['GET'], detail=False)
    def inventory_report(self, request):
        practice = request.query_params.get('practice')
        product = request.query_params.get('product')
        consume = request.query_params.get('consume')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        report_type = request.query_params.get('type')
        queryset = StockEntryItem.objects.filter(read=True, is_active=True, item_add_type="CONSUME")
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
        if practice:
            queryset = queryset.filter(inventory_item__practice=practice)
        if consume:
            consume_list = consume.split(",")
            queryset = queryset.filter(type_of_consumption__in=consume_list)
        if product:
            queryset = queryset.filter(inventory_item=product)
        if report_type == "DAILY":
            queryset = queryset.values('date', 'type_of_consumption') \
                .annotate(year=Year('date'), month=Month('date'), day=Day('date')) \
                .values('day', 'month', 'year', 'type_of_consumption').annotate(consume=Sum('quantity')) \
                .order_by('-year', '-month', '-day', '-consume')
            for res in queryset:
                res['day'] = res['day'].strftime('%d')
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime.datetime(int(res['year']), int(res['month']), int(res['day'])).date()
            return response.Ok(queryset)
        elif report_type == "MONTHLY":
            queryset = queryset.values('date', 'type_of_consumption').annotate(year=Year('date'), month=Month('date')) \
                .values('month', 'year', 'type_of_consumption').annotate(consume=Sum('quantity')) \
                .order_by('-year', '-month', '-consume')
            for res in queryset:
                res['month'] = res['month'].strftime('%m')
                res['year'] = res['year'].strftime('%Y')
                res['date'] = datetime.datetime(int(res['year']), int(res['month']), 1).date()
            return response.Ok(queryset)
        elif report_type == "TOP":
            data = queryset.values('inventory_item__name').annotate(consume=Sum('quantity')) \
                       .values('inventory_item__name', 'consume').order_by('-consume')[:10]
            items = queryset.values('inventory_item').annotate(consume=Sum('quantity')).values('inventory_item',
                                                                                               'consume').order_by(
                '-consume')[:10].values_list('inventory_item', flat=True)
            queryset = queryset.filter(inventory_item__in=items).values('inventory_item__name', 'type_of_consumption') \
                .annotate(consume=Sum('quantity')).values('inventory_item__name', 'consume', 'type_of_consumption') \
                .order_by('-inventory_item')
            return response.Ok({"total": data, "item_wise": queryset})


class StockEntryItemViewSet(ModelViewSet):
    serializer_class = StockEntryItemSerializer
    queryset = StockEntryItem.objects.filter(is_active=True)
    permission_classes = (StockEntryItemPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        supplier = self.request.query_params.get('supplier', None)
        bill_number = self.request.query_params.get('bill_number', None)
        invoice = self.request.query_params.get('invoice', None)
        inventory = self.request.query_params.get('inventory', None)
        queryset = super(StockEntryItemViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True, read=True)
        if start:
            queryset = queryset.filter(date__gte=start)
        if end:
            queryset = queryset.filter(date__lte=end)
        if supplier:
            suppliers = supplier.split(",")
            queryset = queryset.filter(supplier__in=suppliers)
        if invoice and not inventory:
            queryset = queryset.filter(bill_number__contains="INVOICE No:")
        if inventory and not invoice:
            queryset = queryset.exclude(bill_number__contains="INVOICE No:")
        if bill_number:
            queryset = queryset.filter(bill_number__icontains=bill_number)
        return queryset

    @action(methods=['GET'], detail=False)
    def bills_suppliers(self, request, *args, **kwargs):
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        supplier = request.query_params.get('supplier', None)
        bill_number = request.query_params.get('bill_number', None)
        invoice = request.query_params.get('invoice', None)
        inventory = request.query_params.get('inventory', None)
        practice = request.query_params.get('practice', None)
        stock_id = request.query_params.get('id', None)
        queryset = StockEntryItem.objects.filter(is_active=True, read=True)
        if stock_id:
            bill = StockEntryItem.objects.get(id=stock_id)
            bill_number_match = bill.bill_number
            bill_date_start = bill.created_at - timedelta(minutes=1)
            bill_date_end = bill.created_at + timedelta(minutes=1)
            bill_supplier = bill.supplier
            queryset = queryset.filter(bill_number=bill_number_match,
                                       created_at__range=[bill_date_start, bill_date_end], supplier=bill_supplier)
        if start:
            queryset = queryset.filter(date__gte=start)
        if end:
            queryset = queryset.filter(date__lte=end)
        if supplier:
            suppliers = supplier.split(",")
            queryset = queryset.filter(supplier__in=suppliers)
        if invoice and not inventory:
            queryset = queryset.filter(bill_number__contains="INVOICE No:")
        if inventory and not invoice:
            queryset = queryset.exclude(bill_number__contains="INVOICE No:")
        if bill_number:
            queryset = queryset.filter(bill_number__icontains=bill_number)
        if practice:
            queryset = queryset.filter(inventory_item__practice=practice)
        if not stock_id:
            queryset = queryset.distinct('date', 'bill_number')
        page = self.paginate_queryset(queryset)
        if page is not None and not stock_id:
            return self.get_paginated_response(StockEntryItemDistinctSerializer(page, many=True).data)
        return response.Ok(StockEntryItemSerializer(queryset, many=True).data)

    @action(methods=['POST'], detail=False)
    def bulk(self, request):
        request_data_list = request.data
        for data in request_data_list:
            serializer = StockEntryItemSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
        return response.Ok(StockEntryItemSerializer(instance).data)

    @action(methods=['GET'], detail=False)
    def practice_supplier(self, request):
        practice = request.query_params.get('practice')
        if practice:
            return response.Ok(
                SupplierSerializer(Supplier.objects.filter(practice=practice, is_active=True), many=True).data)
        else:
            return response.BadRequest({"detail": "Please Send practice in query params"})


class ItemTypeStockViewSet(ModelViewSet):
    serializer_class = ItemTypeStockSerializer
    queryset = ItemTypeStock.objects.all()
    permission_classes = (ItemTypeStockPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ItemTypeStockViewSet, self).get_queryset()
        return queryset

    @action(methods=['GET'], detail=False)
    def find_item(self, request, *args, **kwargs):
        qr = request.query_params.get("qr", "")
        form = request.query_params.get("form", None)
        qr_detail = qr.split("*")
        if len(qr_detail) == 4 and form:
            name = qr_detail[0]
            batch = qr_detail[1]
            expiry_date = qr_detail[2]
            unit_cost = qr_detail[3]
            data = ItemTypeStock.objects.filter(inventory_item__name=name, batch_number=batch, is_active=True).first()
            if data:
                return response.Ok(InventoryItemSerializer(data.inventory_item).data)
            elif form == "Inventory":
                item = InventoryItem.objects.filter(name=name, is_active=True).first()
                if item:
                    yy = int("20" + expiry_date.split("/")[1])
                    mm = int(expiry_date.split("/")[0])
                    taxes = item.taxes.all()
                    total_tax = 0
                    for tax in taxes:
                        total_tax += tax.tax_value
                    total_tax = 1 + (total_tax / 100)
                    unit_cost = float(unit_cost) / total_tax
                    data = {"batch_number": batch, "inventory_item": item.pk, "item_type": "Drug", "quantity": 0,
                            "expiry_date": datetime.datetime(yy, mm, 1).date(), "item_add_type": "ADD",
                            "unit_cost": round(unit_cost, 2)}
                    serializer = StockEntryItemSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    item = InventoryItem.objects.filter(name=name, is_active=True).first()
                    return response.Ok(InventoryItemSerializer(item).data)
                else:
                    return response.BadRequest({"detail": "No Such Item with this name Exists"})
            else:
                return response.BadRequest({"detail": "Invalid QR Code. Please add it to inventory first."})
        elif not form:
            return response.BadRequest({"detail": "Please Send a source form"})
        else:
            return response.BadRequest({"detail": "Please Send a Valid QR Code"})
