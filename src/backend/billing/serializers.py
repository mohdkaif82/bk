from datetime import datetime
from itertools import groupby
from operator import itemgetter

import pandas as pd
from ..base.serializers import ModelSerializer, serializers
from ..constants import CONST_MEMBERSHIP, CONST_REGISTRATION
from ..inventory.models import ItemTypeStock, StockEntryItem, InventoryItem
from ..inventory.serializers import InventoryItemInvoiceSerializer, StockEntryItemSerializer
from ..mlm.models import ProductMargin, RoleComission
from ..patients.models import PatientWallet, PatientWalletLedger, ProcedureCatalogReturn, InventoryCatalogReturn, \
    ReturnPayment, PatientsPromoCode, PatientInvoices, PatientPayment, InvoiceDetails, Patients, CalculateMlm, \
    InventoryCatalogInvoice, ProcedureCatalogInvoice, Reservations, PatientInventory, MedicineBooking
from ..patients.serializers import PatientsBasicDataSerializer, PatientsReferalSerializer
from ..practice.models import PaymentModes, PracticeStaff
from ..practice.serializers import PracticeBasicSerializer, TaxesSerializer, PracticeStaffBasicSerializer, \
    ProcedureCatalogSerializer, BedBookingPackageDataSerializer, PaymentModesSerializer, OtherDiseasesSerializer, \
    MedicineBookingPackageDataSerializer
from ..utils import sms
from django.contrib.auth import get_user_model
from django.db.models import Sum, Max
from django.utils import timezone

from .models import PatientProformaInvoices, InventoryCatalogProforma, ProcedureCatalogProforma


class ProcedureCatalogInvoiceSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    doctor_data = serializers.SerializerMethodField()
    procedure_data = serializers.SerializerMethodField()
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureCatalogInvoice
        fields = '__all__'

    def get_doctor_data(self, obj):
        data = PracticeStaffBasicSerializer(obj.doctor).data
        return data

    def get_procedure_data(self, obj):
        data = ProcedureCatalogSerializer(obj.procedure).data
        return data

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class InventoryCatalogInvoiceSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    doctor_data = serializers.SerializerMethodField()
    inventory_item_data = serializers.SerializerMethodField()
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCatalogInvoice
        fields = '__all__'

    def get_doctor_data(self, obj):
        data = PracticeStaffBasicSerializer(obj.doctor).data
        return data

    def get_inventory_item_data(self, obj):
        data = InventoryItemInvoiceSerializer(obj.inventory).data
        return data

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class InventoryCatalogInvoiceReportSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()
    doctor_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCatalogInvoice
        fields = '__all__'

    def get_taxes_data(self, obj):
        return TaxesSerializer(obj.taxes, many=True).data

    def get_doctor_data(self, obj):
        return PracticeStaffBasicSerializer(obj.doctor).data


class ProcedureCatalogInvoiceReportSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureCatalogInvoice
        fields = '__all__'

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class PatientWalletSerializer(ModelSerializer):
    class Meta:
        model = PatientWallet
        fields = '__all__'


class PatientWalletDataSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = PatientWallet
        fields = '__all__'


class PatientWalletLedgerDataSerializer(ModelSerializer):
    patient = PatientsBasicDataSerializer(required=False)
    practice = PracticeBasicSerializer(required=False)

    class Meta:
        model = PatientWalletLedger
        fields = '__all__'


class PatientWalletLedgerSerializer(ModelSerializer):
    received_from = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientWalletLedger
        fields = '__all__'

    def create(self, validated_data):
        patient = validated_data['patient']
        try:
            wallet = PatientWallet.objects.get(patient=patient)
        except:
            PatientWallet.objects.create(patient=patient)
            wallet = PatientWallet.objects.get(patient=patient)
        ledger_type = validated_data.get("ledger_type", None)
        amount_type = validated_data.get("amount_type", None)
        amount = validated_data.get("amount", 0)
        refundable_amount = wallet.refundable_amount if wallet.refundable_amount else 0
        non_refundable = wallet.non_refundable if wallet.non_refundable else 0
        if ledger_type == 'Payout' and amount_type == 'Refundable' and amount > refundable_amount:
            raise serializers.ValidationError({"detail": "This amount is not available in wallet"})
        if ledger_type == 'Payout' and amount_type == 'Non Refundable' and amount > non_refundable:
            raise serializers.ValidationError({"detail": "This amount is not available in wallet"})
        ledger = PatientWalletLedger.objects.create(**validated_data)
        if ledger.ledger_type == 'Credit' and ledger.amount_type == 'Refundable':
            wallet.refundable_amount = refundable_amount + ledger.amount
        elif ledger.ledger_type == 'Credit' and ledger.amount_type == 'Non Refundable':
            wallet.non_refundable = non_refundable + ledger.amount
        elif ledger.ledger_type == 'Debit' and ledger.amount_type == 'Refundable':
            wallet.refundable_amount = refundable_amount - ledger.amount
        elif ledger.ledger_type == 'Debit' and ledger.amount_type == 'Non Refundable':
            wallet.non_refundable = non_refundable - ledger.amount
        elif ledger.ledger_type == 'Payout' and ledger.amount_type == 'Refundable':
            wallet.refundable_amount = refundable_amount - ledger.amount
        elif ledger.ledger_type == 'Payout' and ledger.amount_type == 'Non Refundable':
            wallet.non_refundable = non_refundable - ledger.amount
        wallet.save()
        return ledger

    def update(self, instance, validated_data):
        if instance:
            ledger = instance
            if "is_cancelled" in validated_data and ledger.is_cancelled == False and validated_data[
                "is_cancelled"] == True:
                patient = instance.patient
                try:
                    wallet = PatientWallet.objects.get(patient=patient)
                except:
                    raise serializers.ValidationError("Wallet for this patient does not exists")
                ledger_data = PatientWalletLedgerSerializer(ledger).data
                if ledger.ledger_type == 'Credit' and ledger.amount_type == 'Refundable':
                    ledger_data["ledger_type"] = 'Debit'
                elif ledger.ledger_type == 'Credit' and ledger.amount_type == 'Non Refundable':
                    ledger_data["ledger_type"] = 'Debit'
                elif ledger.ledger_type == 'Debit' and ledger.amount_type == 'Refundable':
                    ledger_data["ledger_type"] = 'Credit'
                elif ledger.ledger_type == 'Debit' and ledger.amount_type == 'Non Refundable':
                    ledger_data["ledger_type"] = 'Credit'
                elif ledger.ledger_type == 'Payout' and ledger.amount_type == 'Refundable':
                    ledger_data["ledger_type"] = 'Credit'
                elif ledger.ledger_type == 'Payout' and ledger.amount_type == 'Non Refundable':
                    ledger_data["ledger_type"] = 'Credit'
                wallet.save()
                serializer = PatientWalletLedgerSerializer(data=ledger_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        else:
            raise serializers.ValidationError({"detail": "Send Wallet Ledger Id with data"})
        return instance

    def get_received_from(self, obj):
        patient_id = obj.invoice.patient if obj.invoice and obj.invoice.patient else None
        return PatientsReferalSerializer(patient_id).data if patient_id else None


class ProcedureCatalogReturnSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureCatalogReturn
        fields = '__all__'

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class InventoryCatalogReturnSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCatalogReturn
        fields = '__all__'

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class ReturnPaymentSerializer(ModelSerializer):
    advance_value = serializers.FloatField(required=False)
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)
    procedure = ProcedureCatalogReturnSerializer(many=True, required=False)
    inventory = InventoryCatalogReturnSerializer(many=True, required=False)

    class Meta:
        model = ReturnPayment
        fields = '__all__'

    def create(self, validated_data):
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        advance_value = validated_data.pop("advance_value", None)
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        if user:
            validated_data["staff"] = PracticeStaff.objects.filter(user=user).first()
        practice_obj = validated_data["practice"] if "practice" in validated_data and validated_data[
            "practice"] else None
        prefix = practice_obj.return_prefix if practice_obj and practice_obj.return_prefix else ""
        validated_data["return_id"] = prefix + str(ReturnPayment.objects.filter(practice=practice_obj).count() + 1)
        return_pay = ReturnPayment.objects.create(**validated_data)
        invoice = validated_data.get("invoice", None)
        invoice_data = PatientInvoicesDataSerializer(invoice).data
        for single_procedure in procedures:
            procedure_inv_obj = single_procedure.get("procedure_inv", None)
            unit = single_procedure.get("unit", None)
            for i in range(len(invoice_data["procedure"])):
                single_inv = invoice_data["procedure"][i]
                if procedure_inv_obj and single_inv["id"] == procedure_inv_obj.pk:
                    if unit and procedure_inv_obj.unit and unit == procedure_inv_obj.unit:
                        del invoice_data["procedure"][i]
                        break
                    else:
                        single_inv["unit"] = procedure_inv_obj.unit - unit
            taxes = single_procedure.pop("taxes", None)
            procedure_obj = ProcedureCatalogReturn.objects.create(**single_procedure)
            if taxes:
                procedure_obj.taxes.set(taxes)
            return_pay.procedure.add(procedure_obj)
        for single_inventory in inventorys:
            inventory_inv_obj = single_inventory.get("inventory_inv", None)
            unit = single_inventory.get("unit", None)
            for i in range(len(invoice_data["inventory"])):
                single_inv = invoice_data["inventory"][i]
                if inventory_inv_obj and single_inv["id"] == inventory_inv_obj.pk:
                    if unit and inventory_inv_obj.unit and unit == inventory_inv_obj.unit:
                        del invoice_data["inventory"][i]
                        break
                    else:
                        single_inv["unit"] = inventory_inv_obj.unit - unit
            taxes = single_inventory.pop("taxes", None)
            inventory_obj = InventoryCatalogReturn.objects.create(**single_inventory)
            if taxes:
                inventory_obj.taxes.set(taxes)
            inventory_obj.save()
            return_pay.inventory.add(inventory_obj)
        inv_serializer = PatientInvoicesDataSerializer(instance=invoice, data=invoice_data, partial=True)
        inv_serializer.is_valid(raise_exception=True)
        inv_serializer.save()
        self.calculate_final(return_pay.pk)
        if advance_value and advance_value > 0:
            payment_data = {
                "practice": validated_data.get("practice", None).pk if validated_data.get("practice", None) else None,
                "patient": validated_data.get("patient", None).pk if validated_data.get("patient", None) else None,
                "staff": validated_data.get("staff", None).pk if validated_data.get("staff", None) else None,
                "is_advance": True,
                "is_active": True,
                "advance_value": advance_value,
                "date": datetime.today().date(),
                "type": "Return",
                "return_pay": return_pay.pk
            }
            serializer_benefit = PatientPaymentSerializer(data=payment_data, partial=True)
            serializer_benefit.is_valid(raise_exception=True)
            serializer_benefit.save()
        return return_pay

    def update(self, instance, validated_data):
        is_cancelled = validated_data.get("is_cancelled", None)
        cancel_note = validated_data.get("cancel_note", None)
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        if is_cancelled and instance.is_cancelled == is_cancelled:
            raise serializers.ValidationError({"detail": "This Return Note is already Cancelled."})
        invoice = instance.invoice
        invoice_data = PatientInvoicesDataSerializer(invoice).data
        if is_cancelled:
            user = self.context['request'].user.id if self.context.get('request', None) and self.context[
                'request'].user else None
            if user:
                validated_data["staff"] = PracticeStaff.objects.filter(user=user).first()
            return_pay = ReturnPayment.objects.get(id=instance.id)
            for single_procedure in return_pay.procedure.all():
                procedure_id = single_procedure.procedure.pk
                present = False
                for i in range(len(invoice_data["procedure"])):
                    single_inv = invoice_data["procedure"][i]
                    if single_inv["procedure"] == procedure_id:
                        present = True
                        single_inv["unit"] = single_procedure.unit + single_inv["unit"]
                if not present:
                    procedure_data = ProcedureCatalogReturnSerializer(single_procedure).data
                    procedure_data.pop("id", None)
                    invoice_data["procedure"].append(procedure_data)
            for single_inventory in return_pay.inventory.all():
                inventory_id = single_inventory.inventory.pk
                present = False
                for i in range(len(invoice_data["inventory"])):
                    single_inv = invoice_data["inventory"][i]
                    if single_inv["inventory"] == inventory_id and single_inv[
                        "batch_number"] == single_inventory.batch_number:
                        present = True
                        single_inv["unit"] = single_inventory.unit + single_inv["unit"]
                if not present:
                    inventory_data = InventoryCatalogReturnSerializer(single_inventory).data
                    inventory_data.pop("id", None)
                    invoice_data["inventory"].append(inventory_data)
            inv_serializer = PatientInvoicesDataSerializer(data=invoice_data, instance=invoice, partial=True)
            inv_serializer.is_valid(raise_exception=True)
            inv_serializer.save()
            return_obj = ReturnPayment.objects.get(id=instance.id)
            return_obj.is_cancelled = is_cancelled
            return_obj.cancel_note = cancel_note
            return_obj.save()
            PatientPayment.objects.filter(return_pay=instance.id).update(is_cancelled=True)
        return instance

    def calculate_final(self, return_id):
        return_pay = ReturnPayment.objects.get(id=return_id)
        total_cost = 0
        total_discount = 0
        total_tax = 0
        for procedure in return_pay.procedure.all():
            tax_value = 0.0
            gross = procedure.unit * procedure.unit_cost
            total_cost += gross
            discount_val = procedure.discount if procedure.discount else 0
            if procedure.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in procedure.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            procedure.discount_value = discount_val
            procedure.total = net + tax_value
            procedure.tax_value = tax_value
            procedure.save()
        for inventory in return_pay.inventory.all():
            tax_value = 0.0
            gross = inventory.unit * inventory.unit_cost
            total_cost += gross
            discount_val = inventory.discount if inventory.discount else 0
            if inventory.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in inventory.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            inventory.discount_value = discount_val
            inventory.total = net + tax_value
            inventory.tax_value = tax_value
            inventory.save()
        grand_total = total_cost - total_discount + total_tax
        return_pay.cost = total_cost
        return_pay.discount = total_discount
        return_pay.taxes = total_tax
        return_pay.total = grand_total
        if return_pay.with_tax:
            return_pay.return_value = grand_total
        else:
            return_pay.return_value = grand_total - total_tax
        return_pay.save()
        return return_id

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None


class PatientsPromoCodeSerializer(ModelSerializer):
    class Meta:
        model = PatientsPromoCode
        fields = '__all__'

    def validate(self, data):
        code_type = data.get("code_type", "%")
        code_value = data.get("code_value", 0)
        expiry_date = data.get("expiry_date", None)
        if code_type == "%" and code_value > 100:
            raise serializers.ValidationError({"detail": "Discount percentage can not be greater than 100"})
        if expiry_date and pd.to_datetime(expiry_date) <= timezone.now():
            raise serializers.ValidationError({"detail": "Invalid Expiry Date"})
        return data

    def create(self, validated_data):
        patients = validated_data.pop("patients", [])
        code_type = validated_data.get("code_type", "%")
        code_value = validated_data.get("code_value", 0)
        if code_type == "INR":
            validated_data["maximum_discount"] = code_value
        promocode = PatientsPromoCode.objects.create(**validated_data)
        for patient in patients:
            promocode.patients.add(patient)
        promocode.save()
        return promocode

    def update(self, instance, validated_data):
        patients = validated_data.pop("patients", [])
        code_type = validated_data.get("code_type", "%")
        code_value = validated_data.get("code_value", 0)
        if code_type == "INR":
            validated_data["maximum_discount"] = code_value
        PatientsPromoCode.objects.filter(id=instance.pk).update(**validated_data)
        instance = PatientsPromoCode.objects.get(id=instance.pk)
        for patient in patients:
            if not instance.patients.filter(id=patient.pk).exists():
                instance.patients.add(patient)
        instance.save()
        return instance


class InvoiceDetailsSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    invoice_id = serializers.SerializerMethodField(required=False)
    invoice_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = InvoiceDetails
        fields = '__all__'

    def get_invoice_id(self, obj):
        return obj.invoice.invoice_id if obj.invoice and obj.invoice.invoice_id else None

    def get_invoice_data(self, obj):
        return PatientInvoicesDataSerializer(obj.invoice).data if obj.invoice else None


class PatientInvoicesReportSerializer(ModelSerializer):
    procedure = ProcedureCatalogInvoiceReportSerializer(required=False, many=True)
    inventory = InventoryCatalogInvoiceReportSerializer(required=False, many=True)
    reservation_data = serializers.SerializerMethodField(required=False)
    clinic_cost = serializers.SerializerMethodField(required=False)
    patient = PatientsBasicDataSerializer(required=False)

    class Meta:
        model = PatientInvoices
        fields = '__all__'

    def get_reservation_data(self, obj):
        return ReservationsReportSerializer(obj.reservation).data if obj.reservation else None

    def get_invoice_id(self, obj):
        prefix = obj.practice.invoice_prefix if obj.practice and obj.practice.invoice_prefix else ""
        return prefix + str(
            PatientInvoices.objects.filter(practice=obj.practice, id__lte=obj.id).count())

    def get_clinic_cost(self, obj):
        cost = 0
        for item in obj.inventory.all():
            batch_number = item.batch_number
            inventory = item.inventory
            stock = StockEntryItem.objects.filter(batch_number=batch_number, inventory_item=inventory,
                                                  item_add_type="ADD").first()
            cost += stock.unit_cost * item.unit if stock and item.unit else 0
        for item in obj.procedure.all():
            cost += item.unit_cost * item.unit if item.unit_cost and item.unit else 0
            cost += item.tax_value if item.tax_value else 0
            cost -= item.discount_value if item.discount_value else 0
        return cost


class PatientInvoicesGetSerializer(ModelSerializer):
    payments_data = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    procedure = ProcedureCatalogInvoiceSerializer(required=False, many=True)
    inventory = InventoryCatalogInvoiceReportSerializer(required=False, many=True)
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)
    reservation_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientInvoices
        fields = '__all__'

    def get_payments_data(self, obj):
        data = InvoiceDetails.objects.filter(invoice=obj, is_active=True, patientpayment__is_cancelled=False,
                                             patientpayment__is_active=True).aggregate(Sum('pay_amount'))
        return data['pay_amount__sum'] if data else 0

    def get_payments(self, obj):
        invoice_data = InvoiceDetails.objects.filter(invoice=obj, is_active=True, patientpayment__is_cancelled=False,
                                                     patientpayment__is_active=True).values()
        for invoice in invoice_data:
            invoice["payment_mode"] = None
            invoice["date"] = None
            pay_invoice_id = invoice["id"]
            pay_data_mode = PatientPayment.objects.filter(invoices=pay_invoice_id).values().first()
            if pay_data_mode:
                invoice["pay_id"] = pay_data_mode["id"]
                invoice["date"] = pay_data_mode["date"] if "date" in pay_data_mode else None
                obj = PatientPayment.objects.get(id=pay_data_mode["id"])
                invoice["payment_id"] = obj.payment_id
                pay_mode_id = pay_data_mode["payment_mode_id"]
                payment_mode = PaymentModes.objects.filter(id=pay_mode_id).values().first()
                if payment_mode:
                    invoice["payment_mode"] = payment_mode["payment_type"]
        return invoice_data

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None

    def get_reservation_data(self, obj):
        return ReservationsDataSerializer(obj.reservation).data if obj.reservation else None


class PatientInvoicesDataSerializer(ModelSerializer):
    payments_data = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    procedure = ProcedureCatalogInvoiceSerializer(required=False, many=True)
    inventory = InventoryCatalogInvoiceSerializer(required=False, many=True)
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)
    reservation_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientInvoices
        fields = '__all__'

    def create(self, validated_data):
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        prescriptions = validated_data.pop("prescription", [])
        stock_data = self.stock_exists(inventorys)
        if stock_data["error"]:
            raise serializers.ValidationError({"detail": stock_data["msg"]})
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        practice_obj = validated_data["practice"] if "practice" in validated_data and validated_data[
            "practice"] else None
        prefix = practice_obj.invoice_prefix if practice_obj and practice_obj.invoice_prefix else ""
        validated_data["invoice_id"] = prefix + str(PatientInvoices.objects.filter(practice=practice_obj).count() + 1)
        staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
        validated_data["staff"] = staff
        invoice = PatientInvoices.objects.create(**validated_data)
        invoice.prescription.set(prescriptions)
        inventory_items = []
        for single_procedure in procedures:
            taxes = single_procedure.pop("taxes", None)
            procedure_obj = ProcedureCatalogInvoice.objects.create(**single_procedure)
            if taxes:
                procedure_obj.taxes.set(taxes)
            invoice.procedure.add(procedure_obj)
        inventory_items = self.create_inventory(inventorys, invoice, inventory_items)
        for prescription in prescriptions:
            for drug in prescription.drugs.filter(is_billed=False):
                inventory_id = drug.inventory
                if inventory_id in inventory_items:
                    PatientInventory.objects.filter(id=drug.id).update(is_billed=True)
        invoice.save()
        self.calculate_final(invoice.id)
        self.calculate_mlm(invoice)
        return invoice

    def update(self, instance, validated_data):
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        prescriptions = validated_data.pop("prescription", [])
        is_cancelled = validated_data.get("is_cancelled", False)
        inv_data = PatientInvoicesDataSerializer(instance).data
        if instance and instance.type and instance.type == CONST_MEMBERSHIP:
            raise serializers.ValidationError({"detail": "Membership invoice cannot be cancelled."})
        if instance and instance.type and instance.type == CONST_REGISTRATION:
            raise serializers.ValidationError({"detail": "Registration invoice cannot be cancelled."})
        if inv_data and "is_cancelled" in inv_data and inv_data["is_cancelled"]:
            raise serializers.ValidationError({"detail": "This invoice is already cancelled."})
        if inv_data and "is_cancelled" in inv_data and inv_data["is_cancelled"] and "payments_data" in inv_data and \
                inv_data["payments_data"] and int(inv_data["payments_data"]) > 0:
            raise serializers.ValidationError(
                {"detail": "There is already a payment corresponding to this invoice. Please Cancel it first."})
        if instance and instance.reservation and is_cancelled:
            reservation_obj = instance.reservation
            reservation_obj.payment_status = "CANCELLED"
            reservation_obj.save()
        stock_data = self.stock_exists(inventorys)
        if stock_data["error"]:
            raise serializers.ValidationError({"detail": stock_data["msg"]})
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
        validated_data["invoice_id"] = instance.invoice_id if instance and instance.invoice_id else ""
        validated_data["staff"] = staff
        PatientInvoices.objects.filter(id=instance.id).update(**validated_data)
        invoice = PatientInvoices.objects.get(id=instance.id)
        inventory_items = []
        invoice.procedure.set([])
        for single_procedure in procedures:
            id = single_procedure.pop("id", None)
            taxes = single_procedure.pop("taxes", None)
            if id:
                ProcedureCatalogInvoice.objects.filter(id=id).update(**single_procedure)
                procedure_obj = ProcedureCatalogInvoice.objects.get(id=id)
            else:
                procedure_obj = ProcedureCatalogInvoice.objects.create(**single_procedure)
            if taxes:
                procedure_obj.taxes.set(taxes)
            invoice.procedure.add(procedure_obj)
        self.delete_inventory(invoice, is_cancelled)
        inventory_items = self.create_inventory(inventorys, invoice, inventory_items)
        for prescription in prescriptions:
            for drug in prescription.drugs.filter(is_billed=False):
                inventory_id = drug.inventory
                if inventory_id in inventory_items:
                    if is_cancelled:
                        PatientInventory.objects.filter(id=drug.id).update(is_billed=False)
                    else:
                        PatientInventory.objects.filter(id=drug.id).update(is_billed=True)
        invoice.save()
        self.calculate_final(invoice.id)
        self.calculate_mlm(invoice)
        return invoice

    def stock_exists(self, inventorys):
        for item in inventorys:
            item["inventory"] = item["inventory"].pk if item["inventory"] else None
        grouper = itemgetter("inventory", "batch_number")
        result = []
        msg = "Items "
        flag = False
        item_details = []
        for key, grp in groupby(sorted(inventorys, key=grouper), grouper):
            temp_dict = dict(zip(["inventory", "batch_number"], key))
            temp_dict["unit"] = sum(item["unit"] for item in grp)
            result.append(temp_dict)
        for item in inventorys:
            item["inventory"] = InventoryItem.objects.get(id=item["inventory"]) if item["inventory"] else None
        for item in result:
            inventory = InventoryItem.objects.get(id=item['inventory'])
            batch_number = item['batch_number']
            unit = item["unit"]
            for single_inventory in inventorys:
                if single_inventory["inventory"] == inventory and single_inventory[
                    "batch_number"] == batch_number and "id" in single_inventory:
                    qty = InventoryCatalogInvoice.objects.filter(id=single_inventory["id"]).values("unit").first()
                    unit = unit - qty["unit"]
            count = ItemTypeStock.objects.filter(inventory_item=inventory, batch_number=batch_number,
                                                 quantity__gte=unit).count()
            if count == 0:
                item_details.append(inventory.name)
                flag = True
        msg += ', '.join(item_details) + " is/are not present in required quantity in Inventory Stock."
        return {'error': flag, "msg": msg}

    def calculate_final(self, invoice_id):
        invoice = PatientInvoices.objects.get(id=invoice_id)
        total_cost = invoice.courier_charge if invoice and invoice.courier_charge else 0
        total_discount = 0
        total_tax = 0
        for procedure in invoice.procedure.all():
            tax_value = 0.0
            punit = procedure.unit if procedure.unit else 0
            punit_cost = procedure.unit_cost if procedure.unit_cost else 0
            gross = punit * punit_cost
            total_cost += gross
            discount_val = procedure.discount if procedure.discount else 0
            if procedure.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in procedure.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            procedure.discount_value = discount_val
            procedure.total = net + tax_value
            procedure.tax_value = tax_value
            procedure.save()
        for inventory in invoice.inventory.all():
            tax_value = 0.0
            gross = inventory.unit * inventory.unit_cost
            total_cost += gross
            discount_val = inventory.discount if inventory.discount else 0
            if inventory.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in inventory.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            inventory.discount_value = discount_val
            inventory.total = net + tax_value
            inventory.tax_value = tax_value
            inventory.save()
        total_cost += invoice.reservation.total_price - invoice.reservation.total_tax if invoice.reservation else 0
        total_tax += invoice.reservation.total_tax if invoice.reservation else 0
        grand_total = total_cost - total_discount + total_tax
        invoice.cost = total_cost
        invoice.discount = total_discount
        invoice.taxes = total_tax
        invoice.total = round(grand_total)
        data = InvoiceDetails.objects.filter(invoice=invoice, is_active=True, patientpayment__is_cancelled=False,
                                             patientpayment__is_active=True).aggregate(Sum('pay_amount'))
        payment_total = data['pay_amount__sum'] if data and data['pay_amount__sum'] else 0
        if grand_total - payment_total < 1:
            invoice.is_pending = False
        else:
            invoice.is_pending = True
        invoice.save()
        return invoice_id

    def delete_inventory(self, invoice, is_cancelled):
        for single_inventory in invoice.inventory.all():
            inventory_item_pk = single_inventory.inventory.pk
            inventory_data = ItemTypeStock.objects.filter(inventory_item=inventory_item_pk,
                                                          batch_number=single_inventory.batch_number).values(
                'expiry_date').first()
            expiry_date = inventory_data['expiry_date'] if inventory_data else None
            patient_id = invoice.patient.custom_id if invoice.patient and invoice.patient.custom_id else ""
            patient_name = invoice.patient.user.first_name if invoice.patient and invoice.patient.user \
                                                              and invoice.patient.user.first_name else ""
            stock_manage_data = {'batch_number': single_inventory.batch_number,
                                 'item_add_type': 'ADD',
                                 'inventory_item': inventory_item_pk,
                                 'quantity': single_inventory.unit,
                                 'unit_cost': single_inventory.unit_cost,
                                 'expiry_date': expiry_date,
                                 'total_cost': single_inventory.unit * single_inventory.unit_cost,
                                 'is_processed': True,
                                 'read': False,
                                 'date': invoice.date,
                                 'bill_number': "INVOICE No: " + str(invoice.invoice_id) + " & Patient Name: " + str(
                                     patient_name) + "(" + patient_id + ")"
                                 }
            stock_serializer = StockEntryItemSerializer(data=stock_manage_data)
            stock_serializer.is_valid(raise_exception=True)
            stock_serializer = stock_serializer.save()
            StockEntryItem.objects.filter(inventory_item=inventory_item_pk,
                                          batch_number=single_inventory.batch_number).update(read=False)
            if not is_cancelled:
                invoice.inventory.set([])
        return

    def calculate_mlm(self, invoice):
        margin_price = {}
        CalculateMlm.objects.filter(invoice=invoice.pk).update(is_active=False)
        for item in invoice.inventory.all():
            margin = item.inventory.margin if item.inventory and item.inventory.margin else None
            if margin and margin.pk in margin_price:
                margin_price[margin.pk] += item.total
            elif margin:
                margin_price[margin.pk] = item.total
        for item in invoice.procedure.all():
            margin = item.procedure.margin if item.procedure and item.procedure.margin else None
            if margin and margin.pk in margin_price:
                margin_price[margin.pk] += item.total
            elif margin:
                margin_price[margin.pk] = item.total
        for margin_id in margin_price.keys():
            margin = ProductMargin.objects.get(id=margin_id)
            total = margin_price[margin_id]
            CalculateMlm.objects.create(invoice=invoice, margin=margin, mlm_amount=total, is_active=True)
        return

    def create_inventory(self, inventorys, invoice, inventory_items):
        for single_inventory in inventorys:
            taxes = single_inventory.pop("taxes", None)
            id = single_inventory.pop("id", None)
            inventory_obj = InventoryCatalogInvoice.objects.create(**single_inventory)
            if taxes:
                inventory_obj.taxes.set(taxes)
            inventory_item_pk = single_inventory.get('inventory', None).pk
            inventory_data = ItemTypeStock.objects.filter(inventory_item=inventory_item_pk,
                                                          batch_number=single_inventory.get('batch_number',
                                                                                            None)).values(
                'expiry_date').first()
            expiry_date = inventory_data['expiry_date'] if inventory_data else None

            patient_id = invoice.patient.custom_id if invoice.patient and invoice.patient.custom_id else ""
            patient_name = invoice.patient.user.first_name if invoice.patient and invoice.patient.user \
                                                              and invoice.patient.user.first_name else ""
            stock_manage_data = {'batch_number': single_inventory.get('batch_number', None),
                                 'item_add_type': 'CONSUME',
                                 'inventory_item': inventory_item_pk,
                                 'quantity': single_inventory.get('unit', 0),
                                 'unit_cost': single_inventory.get('unit_cost', 0),
                                 'expiry_date': expiry_date,
                                 'total_cost': single_inventory.get('quantity', 0) * single_inventory.get('unit_cost',
                                                                                                          0),
                                 'is_processed': True,
                                 'bill_number': "INVOICE No: " + str(invoice.invoice_id) + " & Patient Name: " + str(
                                     patient_name) + "(" + patient_id + ")",
                                 'date': invoice.date}
            stock_serializer = StockEntryItemSerializer(data=stock_manage_data)
            stock_serializer.is_valid(raise_exception=True)
            stock_serializer = stock_serializer.save()
            inventory_obj.stock = stock_serializer
            inventory_obj.save()
            invoice.inventory.add(inventory_obj)
            inventory_items.append(inventory_obj.inventory)
        return inventory_items

    def get_payments_data(self, obj):
        data = InvoiceDetails.objects.filter(invoice=obj, is_active=True, patientpayment__is_cancelled=False,
                                             patientpayment__is_active=True).aggregate(Sum('pay_amount'))
        return data['pay_amount__sum'] if data else 0

    def get_payments(self, obj):
        invoice_data = InvoiceDetails.objects.filter(invoice=obj, is_active=True, patientpayment__is_cancelled=False,
                                                     patientpayment__is_active=True).values()
        for invoice in invoice_data:
            invoice["payment_mode"] = None
            invoice["date"] = None
            pay_invoice_id = invoice["id"]
            pay_data_mode = PatientPayment.objects.filter(invoices=pay_invoice_id).values().first()
            if pay_data_mode:
                invoice["date"] = pay_data_mode["date"] if "date" in pay_data_mode else None
                invoice["pay_id"] = pay_data_mode["id"] if "id" in pay_data_mode else None
                obj = PatientPayment.objects.get(id=pay_data_mode["id"])
                invoice["payment_id"] = obj.payment_id
                pay_mode_id = pay_data_mode["payment_mode_id"]
                payment_mode = PaymentModes.objects.filter(id=pay_mode_id).values().first()
                if payment_mode:
                    invoice["payment_mode"] = payment_mode["payment_type"]
        return invoice_data

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None

    def get_reservation_data(self, obj):
        return ReservationsDataSerializer(obj.reservation).data if obj.reservation else None


class InvoiceDetailsDataSerializer(ModelSerializer):
    payments_till_data = serializers.SerializerMethodField(required=False)
    invoice = PatientInvoicesGetSerializer(required=False)

    class Meta:
        model = InvoiceDetails
        fields = '__all__'

    def get_payments_till_data(self, obj):
        data = InvoiceDetails.objects.filter(invoice=obj.invoice, is_active=True, patientpayment__is_cancelled=False,
                                             patientpayment__is_active=True, id__lt=obj.id).aggregate(
            Sum('pay_amount'))
        return data['pay_amount__sum'] if data else 0


class PatientPaymentSerializer(ModelSerializer):
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    invoices = InvoiceDetailsSerializer(required=False, many=True)
    patient_data = serializers.SerializerMethodField(required=False)
    payment_mode_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientPayment
        fields = '__all__'

    def create(self, validated_data):
        invoices = validated_data.pop("invoices", [])
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
        practice_obj = validated_data["practice"] if "practice" in validated_data and validated_data[
            "practice"] else None
        prefix = practice_obj.payment_prefix if practice_obj and practice_obj.payment_prefix else ""
        validated_data["payment_id"] = prefix + str(PatientPayment.objects.filter(practice=practice_obj).count() + 1)
        validated_data["staff"] = staff
        patient_user = validated_data.get("patient", None).user if validated_data.get("patient", None) else None
        for invoice in invoices:
            inv_id = invoice.get('invoice', None)
            if inv_id:
                invoice_id = inv_id.pk
                invoice_data = PatientInvoices.objects.get(id=invoice_id)
                payment_data = InvoiceDetails.objects.filter(invoice=invoice_id, is_active=True,
                                                             patientpayment__is_cancelled=False,
                                                             patientpayment__is_active=True).aggregate(
                    Sum('pay_amount'))
                invoice_data_total = invoice_data.total if invoice_data and invoice_data.total else 0
                payment_data_sum = payment_data['pay_amount__sum'] if payment_data['pay_amount__sum'] else 0
                if float(invoice_data_total) - float(payment_data_sum) - float(invoice.get('pay_amount', 0)) < -1:
                    raise serializers.ValidationError(
                        {"detail": "payment for invoice no INV" + str(
                            inv_id.invoice_id) + " exceeds invoice grand total."})
                if float(invoice_data_total) - float(payment_data_sum) - float(invoice.get('pay_amount', 0)) < 1:
                    self.pay_mlm_comission(invoice_id, patient_user, user)
                    invoice_data.is_pending = False
                    invoice_data.save()
        payment = PatientPayment.objects.create(**validated_data)
        for invoice in invoices:
            id = invoice.pop('id', None)
            if id:
                InvoiceDetails.objects.filter(id=id).update(**invoice)
            else:
                payment.invoices.add(InvoiceDetails.objects.create(**invoice))
        payment.save()
        sms.prepare_patient_payment_sms(payment)
        return payment

    def update(self, instance, validated_data):
        ###### Return MLM #########
        if instance and instance.type and instance.type == CONST_MEMBERSHIP:
            raise serializers.ValidationError({"detail": "Membership payment cannot be cancelled."})
        db_invoices = instance.invoices.all()
        for db_invoice in db_invoices:
            db_invoice_id = db_invoice.invoice.pk if db_invoice.invoice else None
            if db_invoice_id:
                wallet_ledgers = PatientWalletLedger.objects.filter(invoice=db_invoice_id, is_mlm=True)
                for ledger in wallet_ledgers:
                    ledger_data = PatientWalletLedgerSerializer(ledger).data
                    ledger_data["is_cancelled"] = True
                    ledger_serializer = PatientWalletLedgerSerializer(data=ledger_data, instance=ledger, partial=True)
                    ledger_serializer.is_valid(raise_exception=True)
                    ledger_serializer.save()
        ###### End Return MLM #######
        is_cancelled = validated_data.get("is_cancelled", None)
        if is_cancelled:
            cancel_note = validated_data.get("cancel_note", None)
            db_invoices = instance.invoices.all()
            for db_invoice in db_invoices:
                if db_invoice.invoice:
                    db_invoice.invoice.is_pending = True
                    db_invoice.invoice.save()
                db_invoice.is_active = False
                db_invoice.save()
            instance.is_cancelled = is_cancelled
            instance.cancel_note = cancel_note
            instance.save()
        else:
            patient_user = validated_data.get("patient", None).user if validated_data.get("patient", None) else None
            db_invoices = instance.invoices.all()
            invoices = validated_data.pop("invoices", [])
            user = self.context['request'].user.id if self.context.get('request', None) and self.context[
                'request'].user else None
            staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
            validated_data["staff"] = staff
            validated_data["payment_id"] = instance.payment_id if instance and instance.payment_id else ""
            PatientPayment.objects.filter(id=instance.id).update(**validated_data)
            payment = PatientPayment.objects.get(id=instance.id)
            for db_invoice in db_invoices:
                for invoice in invoices:
                    inv_id = invoice.get("id", None)
                    if inv_id == db_invoice.id:
                        break
                else:
                    payment.invoices.remove(db_invoice)
                    db_invoice.is_active = False
                    db_invoice.invoice.is_pending = True
                    db_invoice.invoice.save()
                    db_invoice.save()
            for invoice in invoices:
                invoice_data_id = invoice.pop("id", None)
                inv_id = invoice.get('invoice', None)
                if inv_id:
                    invoice_id = inv_id.pk
                    invoice_data = PatientInvoices.objects.get(id=invoice_id)
                    payment_data = InvoiceDetails.objects.exclude(id=invoice_data_id).filter(invoice=invoice_id,
                                                                                             is_active=True,
                                                                                             patientpayment__is_cancelled=False,
                                                                                             patientpayment__is_active=True).aggregate(
                        Sum('pay_amount'))
                    invoice_data_total = invoice_data.total if invoice_data and invoice_data.total else 0
                    payment_data_sum = payment_data['pay_amount__sum'] if payment_data['pay_amount__sum'] else 0
                    if float(invoice_data_total) - float(payment_data_sum) - float(invoice.get('pay_amount', 0)) < -1:
                        raise serializers.ValidationError({"detail": "payment for invoice no " + str(
                            inv_id.invoice_id) + " exceeds invoice grand total."})
                    if float(invoice_data_total) - float(payment_data_sum) - float(
                            invoice.get('pay_amount', 0)) < 1:
                        invoice_data.is_pending = False
                        self.pay_mlm_comission(invoice_id, patient_user, user)
                    else:
                        invoice_data.is_pending = True
                    invoice_data.save()
                    if invoice_data_id:
                        InvoiceDetails.objects.filter(id=invoice_data_id).update(**invoice)
                    else:
                        inv_obj = InvoiceDetails.objects.create(**invoice)
                        payment.invoices.add(inv_obj)
                    payment.save()
        return instance

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None

    def get_payment_mode_data(self, obj):
        return PaymentModesSerializer(obj.payment_mode).data if obj.payment_mode else None

    def pay_mlm_comission(self, invoice, user, staff_user):
        max_level = CalculateMlm.objects.filter(is_active=True, invoice=invoice).values('margin__level_count').annotate(
            max_value=Max('margin__level_count'))
        max_level_count = max_level[0]["max_value"] if len(max_level) > 0 and "max_value" in max_level[0] else 0
        user_levels = self.get_user_referal(user, max_level_count)
        max_user_level = len(user_levels)
        calculations = CalculateMlm.objects.filter(is_active=True, invoice=invoice)
        current_invoice = PatientInvoicesDataSerializer(PatientInvoices.objects.get(id=invoice)).data
        practice = current_invoice["practice"] if "practice" in current_invoice and current_invoice[
            "practice"] else None
        invoice_id = current_invoice["invoice_id"] if "invoice_id" in current_invoice and current_invoice[
            "invoice_id"] else ""
        current_staff = PracticeStaff.objects.get(user=staff_user, is_active=True) if staff_user else None
        for calculation in calculations:
            levels = calculation.margin.level_count if calculation.margin and calculation.margin.level_count else 0
            max_loop = levels if levels < max_user_level else max_user_level
            for i in range(int(max_loop)):
                current_level = i + 1
                current_user = user_levels[i]
                current_role = self.check_agent_role(current_user)
                commision = RoleComission.objects.filter(level=current_level, role=current_role,
                                                         margin=calculation.margin, is_active=True).first()
                percentage = commision.commision_percent if commision and commision.commision_percent else 0
                current_patient = Patients.objects.get(user=current_user)
                current_amount = calculation.mlm_amount if calculation and calculation.mlm_amount else 0
                pay_data = {
                    "practice": practice,
                    "staff": current_staff.pk if current_staff else None,
                    "patient": current_patient.pk,
                    "invoice": invoice,
                    "mlm": calculation.pk,
                    "amount": current_amount * percentage / 100,
                    "comments": "MLM amount for " + invoice_id,
                    "ledger_type": "Credit",
                    "amount_type": "Non Refundable",
                    "is_mlm": True
                }
                serializer = PatientWalletLedgerSerializer(data=pay_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()

    def check_agent_role(self, user):
        agent = Patients.objects.filter(user=user, is_agent=True, is_approved=True, is_active=True).first()
        if agent:
            return agent.role
        return None

    def get_user_referal(self, user, max_level):
        users = []
        user_obj = get_user_model().objects.get(mobile=user, is_active=True)
        patient_obj = Patients.objects.filter(user=user_obj, is_active=True, is_agent=True, is_approved=True).first()
        if patient_obj:
            users.append(user_obj)
            max_level -= 1
        for i in range(int(max_level)):
            if user_obj.referer and self.check_agent_role(user_obj.referer):
                users.append(user_obj.referer)
                user_obj = get_user_model().objects.get(mobile=user_obj.referer, is_active=True)
            else:
                break
        return users


class PatientPaymentDataSerializer(ModelSerializer):
    practice = PracticeBasicSerializer(required=False)
    patient = PatientsBasicDataSerializer(required=False)
    invoices = InvoiceDetailsDataSerializer(required=False, many=True)
    total = serializers.SerializerMethodField()
    payment_mode_data = serializers.SerializerMethodField()

    class Meta:
        model = PatientPayment
        fields = '__all__'

    def get_total(self, obj):
        return obj.invoices.all().aggregate(total=Sum('pay_amount'))['total'] or 0

    def get_payment_mode_data(self, obj):
        return PaymentModesSerializer(obj.payment_mode).data if obj.payment_mode else None


class MedicineBookingDataSerializer(ModelSerializer):
    medicine = MedicineBookingPackageDataSerializer(required=False)

    class Meta:
        model = MedicineBooking
        fields = '__all__'


class MedicineBookingSerializer(ModelSerializer):
    medicine_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = MedicineBooking
        fields = '__all__'

    def get_medicine_data(self, obj):
        return MedicineBookingDataSerializer(obj.medicine).data if obj.medicine else None


class ReservationsSerializer(ModelSerializer):
    medicines = MedicineBookingSerializer(required=False, many=True)

    class Meta:
        model = Reservations
        fields = (
            'practice', 'bed_package', 'medicines', 'total_tax', 'total_price', 'seat_type', 'seat_no', 'from_date',
            'to_date', 'payment_mode', 'payment_type', 'patient', 'dialysis', 'creatinine', 'urea_level',
            'report_upload', 'remark', 'rest_diseases', 'date', 'bed_package_price', 'bed_package_tax',
            'other_diseases', 'details', 'name', 'email', 'mobile', 'from_website')

    def create(self, validated_data):
        medicines = validated_data.pop('medicines', [])
        medicine_data = []
        save_data = []
        for medicine in medicines:
            medicine["medicine"] = medicine["medicine"].pk
            serializer = MedicineBookingSerializer(data=medicine, partial=True)
            serializer.is_valid(raise_exception=True)
            medicine_data.append(serializer)
        reservation_obj = Reservations.objects.create(**validated_data)
        for medicine in medicine_data:
            medicine = medicine.save()
            save_data.append(medicine.id)
        reservation_obj.medicines.set(save_data)
        reservation_obj.save()
        return reservation_obj


class ReservationsStaffSerializer(ModelSerializer):
    medicines = MedicineBookingSerializer(required=False, many=True)

    class Meta:
        model = Reservations
        fields = (
            'practice', 'bed_package', 'medicines', 'total_tax', 'total_price', 'seat_type', 'seat_no', 'from_date',
            'to_date', 'payment_mode', 'payment_type', 'patient', 'payment_status', 'dialysis', 'creatinine',
            'urea_level', 'report_upload', 'remark', 'rest_diseases', 'date', 'bed_package_price', 'bed_package_tax',
            'other_diseases', 'details')

    def create(self, validated_data):
        medicines = validated_data.pop('medicines', [])
        medicine_data = []
        save_data = []
        for medicine in medicines:
            medicine["medicine"] = medicine["medicine"].pk
            serializer = MedicineBookingSerializer(data=medicine, partial=True)
            serializer.is_valid(raise_exception=True)
            medicine_data.append(serializer)
        reservation_obj = Reservations.objects.create(**validated_data)
        for medicine in medicine_data:
            medicine = medicine.save()
            save_data.append(medicine.id)
        reservation_obj.medicines.set(save_data)
        reservation_obj.save()
        return reservation_obj


class ReservationsReportSerializer(ModelSerializer):
    bed_package = BedBookingPackageDataSerializer()
    medicines = MedicineBookingDataSerializer(many=True)

    class Meta:
        model = Reservations
        fields = '__all__'


class ReservationsDataSerializer(ModelSerializer):
    bed_package = BedBookingPackageDataSerializer()
    practice = PracticeBasicSerializer()
    patient = PatientsBasicDataSerializer()
    payment_mode = PaymentModesSerializer()
    other_diseases = OtherDiseasesSerializer(many=True, required=False)
    medicines = MedicineBookingSerializer(many=True)
    created = serializers.SerializerMethodField()

    class Meta:
        model = Reservations
        fields = '__all__'

    def get_created(self, obj):
        return obj.created_by.first_name if obj.created_by else None


class ProcedureCatalogProformaSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    doctor_data = serializers.SerializerMethodField()
    procedure_data = serializers.SerializerMethodField()
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureCatalogProforma
        fields = '__all__'

    def get_doctor_data(self, obj):
        data = PracticeStaffBasicSerializer(obj.doctor).data
        return data

    def get_procedure_data(self, obj):
        data = ProcedureCatalogSerializer(obj.procedure).data
        return data

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class InventoryCatalogProformaSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    doctor_data = serializers.SerializerMethodField()
    inventory_item_data = serializers.SerializerMethodField()
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCatalogProforma
        fields = '__all__'

    def get_doctor_data(self, obj):
        data = PracticeStaffBasicSerializer(obj.doctor).data
        return data

    def get_inventory_item_data(self, obj):
        data = InventoryItemInvoiceSerializer(obj.inventory).data
        return data

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class InventoryCatalogProformaReportSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()
    doctor_data = serializers.SerializerMethodField()

    class Meta:
        model = InventoryCatalogProforma
        fields = '__all__'

    def get_taxes_data(self, obj):
        return TaxesSerializer(obj.taxes, many=True).data

    def get_doctor_data(self, obj):
        return PracticeStaffBasicSerializer(obj.doctor).data


class ProcedureCatalogProformaReportSerializer(ModelSerializer):
    taxes_data = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureCatalogProforma
        fields = '__all__'

    def get_taxes_data(self, obj):
        data = TaxesSerializer(obj.taxes, many=True).data
        return data


class PatientProformaInvoicesGetSerializer(ModelSerializer):
    procedure = ProcedureCatalogProformaSerializer(required=False, many=True)
    inventory = InventoryCatalogProformaReportSerializer(required=False, many=True)
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientInvoices
        fields = '__all__'

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None


class PatientProformaInvoicesDataSerializer(ModelSerializer):
    procedure = ProcedureCatalogProformaSerializer(required=False, many=True)
    inventory = InventoryCatalogProformaSerializer(required=False, many=True)
    practice_data = serializers.SerializerMethodField(required=False)
    staff_data = serializers.SerializerMethodField(required=False)
    patient_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = PatientInvoices
        fields = '__all__'

    def create(self, validated_data):
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        prescriptions = validated_data.pop("prescription", [])
        stock_data = self.stock_exists(inventorys)
        if stock_data["error"]:
            raise serializers.ValidationError({"detail": stock_data["msg"]})
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        practice_obj = validated_data["practice"] if "practice" in validated_data and validated_data[
            "practice"] else None
        prefix = practice_obj.proforma_prefix if practice_obj and practice_obj.proforma_prefix else ""
        validated_data["invoice_id"] = prefix + str(
            PatientProformaInvoices.objects.filter(practice=practice_obj).count() + 1)
        staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
        validated_data["staff"] = staff
        invoice = PatientProformaInvoices.objects.create(**validated_data)
        invoice.prescription.set(prescriptions)
        inventory_items = []
        for single_procedure in procedures:
            taxes = single_procedure.pop("taxes", None)
            procedure_obj = ProcedureCatalogProforma.objects.create(**single_procedure)
            if taxes:
                procedure_obj.taxes.set(taxes)
            invoice.procedure.add(procedure_obj)
        self.create_inventory(inventorys, invoice, inventory_items)
        invoice.save()
        self.calculate_final(invoice.id)
        return invoice

    def update(self, instance, validated_data):
        procedures = validated_data.pop("procedure", [])
        inventorys = validated_data.pop("inventory", [])
        prescriptions = validated_data.pop("prescription", [])
        is_cancelled = validated_data.get("is_cancelled", False)
        inv_data = PatientProformaInvoicesDataSerializer(instance).data
        if inv_data and "is_cancelled" in inv_data and inv_data["is_cancelled"]:
            raise serializers.ValidationError({"detail": "This invoice is already cancelled."})
        stock_data = self.stock_exists(inventorys)
        if stock_data["error"]:
            raise serializers.ValidationError({"detail": stock_data["msg"]})
        user = self.context['request'].user.id if self.context.get('request', None) and self.context[
            'request'].user else None
        staff = PracticeStaff.objects.get(user=user, is_active=True) if user else None
        validated_data["invoice_id"] = instance.invoice_id if instance and instance.invoice_id else ""
        validated_data["staff"] = staff
        PatientProformaInvoices.objects.filter(id=instance.id).update(**validated_data)
        invoice = PatientProformaInvoices.objects.get(id=instance.id)
        inventory_items = []
        if not is_cancelled:
            invoice.procedure.set([])
            for single_procedure in procedures:
                id = single_procedure.pop("id", None)
                taxes = single_procedure.pop("taxes", None)
                if id:
                    ProcedureCatalogProforma.objects.filter(id=id).update(**single_procedure)
                    procedure_obj = ProcedureCatalogProforma.objects.get(id=id)
                else:
                    procedure_obj = ProcedureCatalogProforma.objects.create(**single_procedure)
                if taxes:
                    procedure_obj.taxes.set(taxes)
                invoice.procedure.add(procedure_obj)
            invoice.inventory.set([])
            self.create_inventory(inventorys, invoice, inventory_items)
        invoice.save()
        self.calculate_final(invoice.id)
        return invoice

    def stock_exists(self, inventorys):
        for item in inventorys:
            item["inventory"] = item["inventory"].pk if item["inventory"] else None
        grouper = itemgetter("inventory", "batch_number")
        result = []
        msg = "Items "
        flag = False
        item_details = []
        for key, grp in groupby(sorted(inventorys, key=grouper), grouper):
            temp_dict = dict(zip(["inventory", "batch_number"], key))
            temp_dict["unit"] = sum(item["unit"] for item in grp)
            result.append(temp_dict)
        for item in inventorys:
            item["inventory"] = InventoryItem.objects.get(id=item["inventory"]) if item["inventory"] else None
        for item in result:
            inventory = InventoryItem.objects.get(id=item['inventory'])
            batch_number = item['batch_number']
            unit = item["unit"]
            for single_inventory in inventorys:
                if single_inventory["inventory"] == inventory and single_inventory[
                    "batch_number"] == batch_number and "id" in single_inventory:
                    qty = InventoryCatalogProforma.objects.filter(id=single_inventory["id"]).values("unit").first()
                    unit = unit - qty["unit"]
            count = ItemTypeStock.objects.filter(inventory_item=inventory, batch_number=batch_number,
                                                 quantity__gte=unit).count()
            if count == 0:
                item_details.append(inventory.name)
                flag = True
        msg += ', '.join(item_details) + " is/are not present in required quantity in Inventory Stock."
        return {'error': flag, "msg": msg}

    def calculate_final(self, invoice_id):
        invoice = PatientProformaInvoices.objects.get(id=invoice_id)
        total_cost = invoice.courier_charge if invoice and invoice.courier_charge else 0
        total_discount = 0
        total_tax = 0
        for procedure in invoice.procedure.all():
            tax_value = 0.0
            punit = procedure.unit if procedure.unit else 0
            punit_cost = procedure.unit_cost if procedure.unit_cost else 0
            gross = punit * punit_cost
            total_cost += gross
            discount_val = procedure.discount if procedure.discount else 0
            if procedure.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in procedure.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            procedure.discount_value = discount_val
            procedure.total = net + tax_value
            procedure.tax_value = tax_value
            procedure.save()
        for inventory in invoice.inventory.all():
            tax_value = 0.0
            gross = inventory.unit * inventory.unit_cost
            total_cost += gross
            discount_val = inventory.discount if inventory.discount else 0
            if inventory.discount_type == "%":
                discount_val = gross * discount_val / 100
            net = gross - discount_val
            for tax in inventory.taxes.all():
                tax_value += tax.tax_value * net / 100
            total_discount += discount_val
            total_tax += tax_value
            inventory.discount_value = discount_val
            inventory.total = net + tax_value
            inventory.tax_value = tax_value
            inventory.save()
        grand_total = total_cost - total_discount + total_tax
        invoice.cost = total_cost
        invoice.discount = total_discount
        invoice.taxes = total_tax
        invoice.total = round(grand_total)
        invoice.save()
        return invoice_id

    def create_inventory(self, inventorys, invoice, inventory_items):
        for single_inventory in inventorys:
            taxes = single_inventory.pop("taxes", None)
            id = single_inventory.pop("id", None)
            inventory_obj = InventoryCatalogProforma.objects.create(**single_inventory)
            if taxes:
                inventory_obj.taxes.set(taxes)
            inventory_obj.save()
            invoice.inventory.add(inventory_obj)
            inventory_items.append(inventory_obj.inventory)
        return inventory_items

    def get_practice_data(self, obj):
        return PracticeBasicSerializer(obj.practice).data if obj.practice else None

    def get_staff_data(self, obj):
        return PracticeStaffBasicSerializer(obj.staff).data if obj.staff else None

    def get_patient_data(self, obj):
        return PatientsBasicDataSerializer(obj.patient).data if obj.patient else None
