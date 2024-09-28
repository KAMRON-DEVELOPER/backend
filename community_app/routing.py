from django.urls import path
from .consumers import ChatRoomConsumer


websocket_urlpatterns = [
    path("ws/chat/<str:chat_room_name>/", ChatRoomConsumer.as_asgi()),
    # path("ws/group/<str:group_room_name>/", GroupRoomConsumer.as_asgi()),
]
