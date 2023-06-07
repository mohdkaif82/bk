import json

from channels.generic.websocket import WebsocketConsumer

from asgiref.sync import async_to_sync
from django.conf import settings
from .models import ActiveUser,Room,TextMessage
# from django.contrib.auth.models import User
from datetime import datetime,date
from ..accounts.models import User
# User = settings.AUTH_USER_MODEL


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = "chat_%s" % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()
        self.r=Room.objects.get(name=self.room_name)
        self.ac = ActiveUser.objects.get(room= self.r)
        print('active user', self.ac)
        incoming_user = User.objects.get(id=self.user_id)

        # for adding incoming user in active_user of room
        if incoming_user not in self.ac.user.all():
            self.ac.user.add(incoming_user)

        # send all user
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "total_user", 
            "message": self.ac.get_queryset_of_active_user()}
        )


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        to = text_data_json.get("to",None)
        sender = text_data_json["from"]

        # when user is logging out 
        if message=="logout#" :

            self.ac.user.remove(User.objects.get(id=sender))
            print("received logout ",self.ac)
            async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "total_user", 
                "message": self.ac.get_queryset_of_active_user()}
            )
        else:
            TextMessage(room=self.r, text=message, sender_id=int(sender), receiver_id=int(to)).save()
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "chat_message", "message": message, "to":to, "from":sender}
            )
        

    def total_user(self,event):
        print("sending total user ", event["message"])
        message = event["message"]
        self.send(text_data= json.dumps({"message": message,"type":"total_user"}))

    def chat_message(self, event):
        message = event["message"]
        sender = User.objects.get(id=event["from"]).email
        to_username = User.objects.get(id=event["to"]).email
        self.send(text_data=json.dumps(
            {"message": message,"type":"chat_message"
            ,"to":event["to"],"to_username":to_username,"from":event["from"],"sender":sender,"datetime":datetime.now().strftime("%d/%m/%y %H:%M:%S")}
        ))
        