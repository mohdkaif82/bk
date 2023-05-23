# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..base import response
from ..base.api.viewsets import ModelViewSet
from .models import ProductMargin, RoleComission, AgentRole, PointsToBusiness
from .permissions import ProductMarginPermissions, RoleComissionPermissions
from .serializers import ProductMarginSerializer, RoleComissionSerializer, RoleComissionDataSerializer, \
    AgentRoleSerializer, PointsToBusinessSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


from ..patients.services import create_update_record


class ProductMarginViewSet(ModelViewSet):
    serializer_class = ProductMarginSerializer
    queryset = ProductMargin.objects.all()
    permission_classes = (ProductMarginPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(ProductMarginViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(methods=['GET', 'POST'], detail=False)
    def points_to_business(self, request, *args, **kwargs):
        if request.method == 'GET':
            return response.Ok(PointsToBusinessSerializer(
                PointsToBusiness.objects.filter(is_active=True).order_by('-id').first()).data)
        else:
            return response.Ok(create_update_record(request, PointsToBusinessSerializer, PointsToBusiness))

    @action(methods=['GET', 'POST'], detail=False)
    def generate_mlm(self, request, *args, **kwargs):
        if request.method == 'GET':
            margins = ProductMarginSerializer(ProductMargin.objects.filter(is_active=True).order_by('-id'),
                                              many=True).data
            for margin in margins:
                margin_id = margin['id'] if 'id' in margin else None
                if margin_id:
                    comissions = RoleComissionSerializer(
                        RoleComission.objects.filter(margin=margin_id).order_by('level'), many=True).data
                else:
                    comissions = []
                margin["comissions"] = comissions
            return response.Ok(margins)
        else:
            data = request.data.copy()
            comissions = data.pop("comissions", [])
            save_list = []
            product_id = data.pop("id", None)
            if product_id:
                product_obj = ProductMargin.objects.get(id=product_id)
                product_serializer = ProductMarginSerializer(data=data, instance=product_obj)
            else:
                product_serializer = ProductMarginSerializer(data=data)
            product_serializer.is_valid(raise_exception=True)
            product = product_serializer.save()
            product_id = product.id
            if product_id:
                for comission in comissions:
                    level = comission.get("level", None)
                    role = comission.get("role", None)
                    comission["margin"] = product_id
                    if level and product_id and role:
                        try:
                            comission_obj = RoleComission.objects.get(level=level, margin=product_id, role=role)
                            serializer = RoleComissionSerializer(data=comission, instance=comission_obj, partial=True)
                        except:
                            serializer = RoleComissionSerializer(data=comission, partial=True)
                        serializer.is_valid(raise_exception=True)
                        save_list.append(serializer)
                for serializer in save_list:
                    serializer.save()
            return response.Ok({'details': "All the role commision created successfully"})


class RoleComissionViewSet(ModelViewSet):
    serializer_class = RoleComissionSerializer
    queryset = RoleComission.objects.all()
    permission_classes = (RoleComissionPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(RoleComissionViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset

    def list(self, request):
        queryset = RoleComission.objects.all()
        queryset = queryset.filter(is_active=True)
        serializer = RoleComissionDataSerializer(queryset, many=True)
        return response.Ok(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = RoleComission.objects.all()
        queryset = queryset.filter(is_active=True)
        role_commission = get_object_or_404(queryset, pk=pk)
        serializer = RoleComissionDataSerializer(role_commission)
        return response.Ok(serializer.data)

    @action(methods=['GET', 'POST'], detail=False)
    def agent_roles(self, request):
        if request.method == 'GET':
            practice_id = request.query_params.get('practice')
            data = AgentRole.objects.filter(is_active=True)
            if practice_id:
                data = data.filter(practice=practice_id)
            return response.Ok(AgentRoleSerializer(data.order_by('-id'), many=True).data)
        else:
            data = request.data.copy()
            id = data.pop("id", None)
            if id:
                instance = AgentRole.objects.get(id=id)
                serializer = AgentRoleSerializer(instance=instance, data=data, partial=True)
            else:
                serializer = AgentRoleSerializer(data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Ok(serializer.data) if serializer else response.BadRequest({'detail': 'Invalid Request'})
