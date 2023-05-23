from .models import BlockCalendar
from .serializers import BlockCalendarSerializer


def update_block_calendar(request):
    validated_data = request.data.copy()
    calendar_id = validated_data.pop("id", None)
    if calendar_id:
        calendar_obj = BlockCalendar.objects.get(id=calendar_id)
        serializer = BlockCalendarSerializer(instance=calendar_obj, data=validated_data, partial=True)
    else:
        serializer = BlockCalendarSerializer(data=validated_data, partial=True)
    serializer.is_valid(raise_exception=True)
    update_object = serializer.save()
    return BlockCalendarSerializer(update_object).data
