from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Room, RoomMessage


class RoomSerializer(ModelSerializer):

    class Meta:
        model = Room

    fields = ["name", "room_type", "members"]


class RoomMessageSerializer(ModelSerializer):
    room = SerializerMethodField(read_only=True)
    user = SerializerMethodField(read_only=True)

    class Meta:
        model = RoomMessage
        fields = ["room", "user", "text_message", "media_message", "created_time", "updated_time"]

    @staticmethod
    def get_room(obj):
        """return user profession name"""
        return obj.room.name

    @staticmethod
    def get_user(obj):
        """return user profession name"""
        return obj.user.username
