from pyfcm import FCMNotification

fcm = FCMNotification(api_key="AAAAHtExnig:APA91bEcWrrZ1IHwP2SnDy-NdCuzsYlXFZwKRbOD6d5A-rvM1GvVr4rHG1-H2orfUz_OoCKQ53vAuU1puDTE3K7Wc4FmCMmnbk3cVt6dXCMkD8tATqXkC9qNpl9TcYWgskS6PMp87aZz")


def send_noti(message_title,message_body,registration_id):
    result = fcm.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
    print(result)
    
def send_bulk_notification(registration_ids, data):
 
    res=fcm.notify_multiple_devices(registration_ids,data)
    return res
