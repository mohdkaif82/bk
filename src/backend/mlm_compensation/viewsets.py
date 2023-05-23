# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..base import response
from ..base.api.viewsets import ModelViewSet
from .models import ProductMarginAdvisor, RoleComissionAdvisor, PointsToBusinessAdvisor
from .permissions import PointsToBusinessAdvisorPermissions, ProductMarginAdvisorPermissions, RoleComissionAdvisorPermissions
from .serializers import ProductMarginAdvisorSerializer, RoleComissionAdvisorSerializer, RoleComissionDataAdvisorSerializer, \
    PointsToBusinessAdvisorSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


from ..patients.services import create_update_record



class ProductMarginAdvisorViewSet(ModelViewSet):
    serializer_class = ProductMarginAdvisorSerializer
    queryset = ProductMarginAdvisor.objects.all()
    permission_classes = (ProductMarginAdvisorPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ProductMarginAdvisorViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset



    @action(methods=['GET', 'POST'], detail=False)
    def generate_mlm(self, request, *args, **kwargs):
        if request.method == 'GET':
            margins = ProductMarginAdvisorSerializer(ProductMarginAdvisor.objects.filter(is_active=True).order_by('-id').first()).data
            return response.Ok(margins)
        else:
            data = request.data.copy()
            comissions = data.pop("comissions", [])
            save_list = []
            product_id = data.pop("id", None)
            if product_id:
                product_obj = ProductMarginAdvisor.objects.get(id=product_id)
                product_serializer = ProductMarginAdvisorSerializer(data=data, instance=product_obj)
            else:
                product_serializer = ProductMarginAdvisorSerializer(data=data)
            product_serializer.is_valid(raise_exception=True)
            product = product_serializer.save()
            product_id = product.id
            if product_id:
                for comission in comissions:
                    level = comission.get("level", None)
                    comission["margin"] = product_id
                    if level and product_id:
                        try:
                            comission_obj = RoleComissionAdvisor.objects.get(level=level, margin=product_id)
                            serializer = RoleComissionAdvisorSerializer(data=comission, instance=comission_obj, partial=True)
                        except:
                            serializer = RoleComissionAdvisorSerializer(data=comission, partial=True)
                        serializer.is_valid(raise_exception=True)
                        save_list.append(serializer)
                for serializer in save_list:
                    serializer.save()
            return response.Ok({'details': "All the role commision created successfully"})


class RoleComissionAdvisorViewSet(ModelViewSet):
    serializer_class = RoleComissionAdvisorSerializer
    queryset = RoleComissionAdvisor.objects.all()
    permission_classes = (RoleComissionAdvisorPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(RoleComissionAdvisorViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset

    def list(self, request):
        queryset = RoleComissionAdvisor.objects.all()
        queryset = queryset.filter(is_active=True)
        serializer = RoleComissionDataAdvisorSerializer(queryset, many=True)
        return response.Ok(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = RoleComissionAdvisor.objects.all()
        queryset = queryset.filter(is_active=True)
        role_commission = get_object_or_404(queryset, pk=pk)
        serializer = RoleComissionDataAdvisorSerializer(role_commission)
        return response.Ok(serializer.data)


class PointsToBusinessAdvisorViewSet(ModelViewSet):
    serializer_class = PointsToBusinessAdvisorSerializer
    queryset = PointsToBusinessAdvisor.objects.all()
    permission_classes = (PointsToBusinessAdvisorPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(PointsToBusinessAdvisorViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
    
    
    
    @action(methods=['GET', 'POST'], detail=False)
    def points_to_business(self, request, *args, **kwargs):
       if request.method == 'GET':
           return response.Ok(PointsToBusinessAdvisorSerializer(
               PointsToBusinessAdvisor.objects.filter(is_active=True).order_by('-id').first()).data)
       else:
           return response.Ok(create_update_record(request, PointsToBusinessAdvisorSerializer, PointsToBusinessAdvisor))