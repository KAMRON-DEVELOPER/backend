from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, RoomType, RoomMessage


async def create_room(room_name, room_type):
    # Check if the room already exists
    try:
        room = await database_sync_to_async(Room.objects.get)(name=room_name)
    except Room.DoesNotExist:
        room = await database_sync_to_async(Room.objects.create)(name=room_name, room_type=room_type)

    return room


async def save_message(room, user, text_message=None, media_message=None):
    await database_sync_to_async(RoomMessage.objects.create)(
        room=room,
        user=user,
        text_message=text_message,
        media_message=media_message,
    )


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat_room_name = self.scope["url_route"]["kwargs"].get("chat_room_name")

        await self.channel_layer.group_add(
            self.chat_room_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, code):
        print(f"🚨 DISCONNECTED, CODE: {code}")
        await self.channel_layer.group_discard(
            self.chat_room_name,
            self.channel_name,
        )

    async def receive(self, text_data=None, bytes_data=None):
        print(f"TEXT_DATA> {text_data}, TYPE> {type(text_data)}\n BYTES_DATA> {bytes_data[:10]}..., TYPE> {type(bytes_data)}" if bytes_data else f"TEXT_DATA> {text_data}, TYPE> {type(text_data)}\n BYTES_DATA> None, TYPE> None")
        if text_data:
            room = await create_room(self.chat_room_name, RoomType.chat)
            await save_message(room, self.user, text_message=text_data)
            await self.channel_layer.group_send(
                self.chat_room_name,
                {
                    "type": "chat_message",
                    "text_data": text_data,
                }
            )
        if bytes_data:
            room = await create_room(self.chat_room_name, RoomType.chat)
            await save_message(room, self.user, media_message=bytes_data)
            await self.channel_layer.group_send(
                self.chat_room_name,
                {
                    "type": "media_message",
                    "bytes_data": bytes_data,
                }
            )

    async def chat_message(self, event):
        text_message = event["text_data"]
        print(f"EVENT> {event}, TYPE> {type(event)}\n TEXT_MESSAGE> {text_message}, TYPE> {type(text_message)}")

        await self.send(text_data=text_message)

    async def media_message(self, event):
        bytes_message = event["bytes_data"]
        print(f"EVENT> {event}, TYPE> {type(event)}\n BYTES_MESSAGE> {bytes_message[:10]}..., TYPE> {type(bytes_message)}")

        await self.send(bytes_data=bytes_message)
