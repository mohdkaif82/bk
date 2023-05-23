from ..base.serializers import ModelSerializer, serializers
from .models import PointsToBusinessAdvisor,  ProductMarginAdvisor, RoleComissionAdvisor


class PointsToBusinessAdvisorSerializer(ModelSerializer):
    class Meta:
        model = PointsToBusinessAdvisor
        fields = '__all__'



class ProductMarginAdvisorSerializer(ModelSerializer):
    class Meta:
        model = ProductMarginAdvisor
        fields = '__all__'

    def get_comissions(self, obj):
        return RoleComissionAdvisorSerializer(
            RoleComissionAdvisor.objects.filter(margin=obj.id).order_by('level'), many=True).data
            

class RoleComissionAdvisorSerializer(ModelSerializer):
    class Meta:
        model = RoleComissionAdvisor
        fields = '__all__'


class RoleComissionDataAdvisorSerializer(ModelSerializer):
    margin = ProductMarginAdvisorSerializer(required=False)

    class Meta:
        model = RoleComissionAdvisor
        fields = '__all__'

