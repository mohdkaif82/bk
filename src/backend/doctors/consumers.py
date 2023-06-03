import json
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import time
import base64
from PIL import Image
from io import BytesIO
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from web socket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data['room']
        
        if data['file']:
            file =data['file']
            print(type(file),file)
            binary_data = base64.b64decode(file)
            image_data = BytesIO(binary_data)
            image = Image.open(image_data)
            image_name=str(time.time())
            image_path = f'media/usermessages/file/{image_name}.jpg'
            image.save(image_path)
            await self.save_message(username, room, message,f'/usermessages/file/{image_name}.jpg')
            await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'file':f'/usermessages/file/{image_name}.jpg'
            }
            
        )
            await self.save_message(username, room, message)
        else:
            await self.save_message(username, room, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
               
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        try:
            message = event['message']
            username = event['username']
            image=event['file']

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'image': image,
            }))
        except:
            message = event['message']
            username = event['username']
            # image=event['file']

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                # 'image': image,
            }))
            

    @sync_to_async
    def save_message(self, username, room, message,file=None):
        Message.objects.create(username=username, room=room, content=message,file=file)
        
        
