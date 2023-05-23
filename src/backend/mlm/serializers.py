from ..base.serializers import ModelSerializer, serializers
from .models import PointsToBusiness, ProductMargin, RoleComission, AgentRole


class PointsToBusinessSerializer(ModelSerializer):
    class Meta:
        model = PointsToBusiness
        fields = '__all__'

class ProductMarginSerializer(ModelSerializer):
    class Meta:
        model = ProductMargin
        fields = '__all__'


class RoleComissionSerializer(ModelSerializer):
    class Meta:
        model = RoleComission
        fields = '__all__'


class RoleComissionDataSerializer(ModelSerializer):
    margin = ProductMarginSerializer(required=False)

    class Meta:
        model = RoleComission
        fields = '__all__'


class AgentRoleSerializer(ModelSerializer):
    class Meta:
        model = AgentRole
        fields = '__all__'
