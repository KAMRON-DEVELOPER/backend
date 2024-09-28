from django.utils import timezone
from asgiref.sync import sync_to_async
from rest_framework import permissions, status
from rest_framework.response import Response
from adrf.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from shared_app.utils import user_credential_generator
from .models import CustomUser, Note, Tab
from config.firebase_auth import custom_firebase_validation
from asyncio import to_thread
from functools import partial
from .serializers import (
    CustomUserSerializer,
    CustomUsersSerializer,
    LoginSerializer,
    NoteSerializer,
    RegisterSerializer,
    VerificationSerializer,
    TabSerializer,
)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    async def post(self, request):
        register_serializer = RegisterSerializer(data=request.data, request=request, many=False)

        if await to_thread(register_serializer.is_valid, raise_exception=True):
            return Response(await register_serializer.validated_data, status=status.HTTP_200_OK)


class VerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    async def post(self, request):
        verify_serializer = VerificationSerializer(data=request.data, request=request)

        if await to_thread(verify_serializer.is_valid, raise_exception=True):
            return Response(await verify_serializer.validated_data, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    async def post(self, request):
        login_serializer = LoginSerializer(data=request.data, request=request, many=False)

        if await to_thread(login_serializer.is_valid, raise_exception=True):
            return Response(await login_serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    async def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "you must send refresh token.", "code": "no_refresh_token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = await to_thread(partial(RefreshToken, refresh_token))
        except InvalidToken:
            return Response({"detail": "Invalid token.", "code": "invalid_token"}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({"detail": str(e), "code": "invalid_token"}, status=status.HTTP_400_BAD_REQUEST)

        current_timestamp = int(timezone.now().timestamp())
        print(f"current_timestamp >> {current_timestamp}")
        print(f"current_time >> {timezone.datetime.fromtimestamp(current_timestamp)}")

        if refresh.payload.get("exp") > current_timestamp:
            await to_thread(refresh.blacklist)

        return Response(status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    async def get(self, request):
        user = request.user
        profile_serializer = CustomUserSerializer(user, many=False)
        return Response(await profile_serializer.adata, status=status.HTTP_200_OK)

    async def patch(self, request):
        user = request.user
        update_serializer = CustomUserSerializer(instance=user, data=request.data, partial=True)
        if await to_thread(update_serializer.is_valid, raise_exception=True):

            await update_serializer.asave()

            return Response({"detail": "Profile updated!", "code": "profile_updated"}, status=status.HTTP_200_OK)

    async def delete(self, request):
        user = request.user
        await sync_to_async(user.delete)()
        return Response(status=status.HTTP_200_OK)


class TabAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        tabs = user.tabs.all()
        tabs_serializer = TabSerializer(tabs, many=True)
        tabs = tabs_serializer.data
        for tab in tabs:
            tab.pop('owner', None)
        print(f"tabs_serializer >> {tabs_serializer.data}")
        return Response(tabs, status=status.HTTP_200_OK)

    def post(self, request):
        print(f"user >> {request.user}, data >> {request.data}")
        tab_serializer = TabSerializer(data=request.data, context={'owner': request.user})
        if tab_serializer.is_valid():
            tab_serializer.save()
            tab = tab_serializer.data
            tab.pop('owner', None)
            return Response(tab, status=status.HTTP_201_CREATED)
        return Response(tab_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        tab_id = request.data.get("id")
        print(f"user >> {request.user}\n tab_id >> {tab_id}")
        tab = Tab.objects.get(id=tab_id, owner=request.user)
        serializer = TabSerializer(tab, data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        note = Note.objects.get(id=request.data["id"])
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notes = request.user.notes.filter(category=None)
        print(f'user >> {request.user}\n notes >> {notes}')
        notes_serializer = NoteSerializer(notes, many=True)
        notes = notes_serializer.data
        for note in notes:
            note.pop("owner", None)
        return Response(notes, status=status.HTTP_200_OK)

    def post(self, request):
        print(f"data >> {request.data}\n user >> {request.user}")
        serializer = NoteSerializer(data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            new_note = serializer.data
            new_note.pop('owner', None)
            return Response(new_note, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        print(f"user >> {user}\n tab_id >> {request.data.get('id')}")
        tab = Tab.objects.get(id=request.data.get("id"), owner=request.user)
        serializer = TabSerializer(tab, data=request.data, context={"owner": request.user}, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        tab = Tab.objects.get(id=request.data["id"])
        tab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUsersAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    async def get(self, request):
        users = await sync_to_async(CustomUser.objects.all)()
        users_serializers = CustomUsersSerializer(users, many=True)
        return Response(await users_serializers.adata, status=status.HTTP_200_OK)


class FirebaseSocialAuthAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    async def post(self, request):
        print(f"📝 REQUEST: {request}")
        firebase_id_token = request.data["firebase_id_token"]
        validate = await custom_firebase_validation(firebase_id_token)
        if validate is not None:
            firebase_user_display_name, firebase_user_email, firebase_user_phone_number, firebase_user_photo_url = (
                validate.get(key) for key in ("display_name", "email", "phone_number", "photo_url")
            )

            generated_username = await to_thread(user_credential_generator, "username", firebase_user_display_name),
            generated_password = await to_thread(partial(user_credential_generator, "password")),
            generated_avatar_url = await to_thread(
                user_credential_generator,
                "avatar", firebase_user_photo_url,  # generated_username=generated_username,
            ),

            print(f"📝 generated_username: {generated_username}")
            print(f"📝 generated_password: {generated_password}")
            print(f"📝 generated_avatar_url: {generated_avatar_url}")

            user, created = await sync_to_async(CustomUser.objects.get_or_create)(
                email=firebase_user_email,
                defaults={
                    "username": generated_username,
                    "password": generated_password,
                    "phone_number": firebase_user_phone_number,
                    "avatar": generated_avatar_url,
                }
            )

            if created:
                created_user_serializer = CustomUserSerializer(user, many=False)
                try:
                    print(f"🥳 created user: {created_user_serializer.data}")
                    print(f"🥳 created user: {await created_user_serializer.adata}")
                except Exception as e:
                    print(f"❌ error: {e}")
                return Response(created_user_serializer.data, status=status.HTTP_200_OK)

            user_serializer = CustomUserSerializer(user, many=False)
            return Response(user_serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"message": "Bad"}, status=status.HTTP_400_BAD_REQUEST)
