import django_filters
from .models import Conversion, DiseaseList, SymptomList, Medicines, DynamicData, CareersApplication, \
    DiseaseCategory


class ConversionFilter(django_filters.FilterSet):
    class Meta:
        model = Conversion
        fields = [field.name for field in model._meta.fields]


class DiseaseListFilter(django_filters.FilterSet):
    class Meta:
        model = DiseaseList
        fields = [field.name for field in model._meta.fields]


class DiseaseCategoryFilter(django_filters.FilterSet):
    class Meta:
        model = DiseaseCategory
        fields = [field.name for field in model._meta.fields]


class SymptomListFilter(django_filters.FilterSet):
    class Meta:
        model = SymptomList
        fields = [field.name for field in model._meta.fields]


class DynamicDataFilter(django_filters.FilterSet):
    class Meta:
        model = DynamicData
        fields = [field.name for field in model._meta.fields]


class CareersApplicationFilter(django_filters.FilterSet):
    class Meta:
        model = CareersApplication
        fields = [field.name for field in model._meta.fields]


class MedicinesFilter(django_filters.FilterSet):
    name_contains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    type_contains = django_filters.CharFilter(field_name='medicine_type', lookup_expr='icontains')

    class Meta:
        model = Medicines
        fields = [field.name for field in model._meta.fields]
