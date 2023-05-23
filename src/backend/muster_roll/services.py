def create_update_multiple_record(data, serializer_class, model_class):
    result = []
    save_data = []
    for request_data in data:
        data_id = request_data.pop('id', None)
        if data_id:
            data_obj = model_class.objects.get(id=data_id)
            serializer = serializer_class(instance=data_obj, data=request_data, partial=True)
        else:
            serializer = serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        result.append(serializer)
    for item in result:
        save_data.append(serializer_class(instance=item.save()).data)
    return save_data
