from django.urls import path
from .views import ChatRoomAPIView, GroupRoomAPIView


urlpatterns = [
    path("chat/<str:chat_room_name>/", ChatRoomAPIView.as_view()),
    path("group/<str:group_room_name>/", GroupRoomAPIView.as_view()),
]
