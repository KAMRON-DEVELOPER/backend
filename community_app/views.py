from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Room, RoomMessage
from .serializers import RoomMessageSerializer


class ChatRoomAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            chat_room_name = request.headers.get("chat-room-name")
            room = Room.objects.get(name=chat_room_name)
            messages = RoomMessage.objects.filter(room=room).order_by("created_time")
            serializer = RoomMessageSerializer(messages, many=True)
            print(f"SERIALIZER.DATA: {serializer.data}\n CHAT_ROOM_NAME: {chat_room_name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_400_BAD_REQUEST)


class GroupRoomAPIView(APIView):
    def get(self, request):
        text_messages = RoomMessage.objects.get()
        print(f"TEXT_MESSAGES: {text_messages}")
