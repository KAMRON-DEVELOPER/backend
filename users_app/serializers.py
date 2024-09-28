from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from adrf.serializers import ModelSerializer, Serializer
from .models import AuthType, CustomUser, Note, Tab, Profession
from django.contrib.auth import authenticate
from .tasks import send_email_or_sms
from django.core.cache import cache
import random
from uuid import uuid4
import json
from asgiref.sync import sync_to_async
from shared_app.serializer_validator import CustomSerializerValidator


def get_temporary_user_token(request, for_verify=False):
    temporary_user_token = request.headers.get("temporary-user-token")

    if not temporary_user_token and for_verify:
        raise ValidationError({"error": "Don't hack me bro."})

    return temporary_user_token


async def get_extended_register_data(temporary_user_token, for_verify=False):
    json_extended_register_data = await cache.aget(temporary_user_token)
    print("📝 json_extended_register_data in get_extended_register_data", json_extended_register_data)

    if json_extended_register_data is None:
        if for_verify:
            raise ValidationError({"error": "The code has expired or you provided an invalid code."})
        return None

    try:
        extended_register_data = json.loads(json_extended_register_data)
        print("📝 extended_register_data in get_extended_register_data ", extended_register_data)
        return extended_register_data
    except json.JSONDecodeError:
        print("error in get_extended_register_data :::: JSONDecodeError")
        raise ValidationError({"error": "The code has expired or you provided an invalid code."})


class RegisterSerializer(Serializer):
    username = serializers.CharField(required=False, allow_null=True)
    password = serializers.CharField(required=False, allow_null=True)
    auth_type = serializers.CharField(required=False, allow_null=True)
    email = serializers.CharField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    async def validate(self, data):
        is_user_exist = False
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        phone_number = data.get("phone_number")
        auth_type = data.get("auth_type")

        if username is None:
            raise ValidationError({"detail": "Please provide a username.", "status": "username_required"})
        if password is None:
            raise ValidationError({"detail": "Please provide a password.", "status": "password_required"})
        if auth_type is None or auth_type not in [AuthType.email, AuthType.phone]:
            raise ValidationError(
                {"detail": "Please provide either an email or a phone number.", "status": "auth_type_required"}
            )

        temporary_user_token = get_temporary_user_token(self.request)
        extended_register_data = await get_extended_register_data(temporary_user_token)
        print("1.0) 📝temporary_user_token >> ", temporary_user_token, type(temporary_user_token))
        print("1.1) 📝extended_register_data >> ", extended_register_data, type(extended_register_data))

        if extended_register_data and temporary_user_token in extended_register_data:
            print("2.0) 🥶temporary_user_token has in the json_extended_register_data")
            raise ValidationError({"detail": "Your code has not expired."})

        # TODO validate basic fields
        if auth_type == AuthType.email:
            is_user_exist = await sync_to_async(
                CustomUser.objects.filter(Q(username=username) | Q(email=email)).exists
            )()
        elif auth_type == AuthType.phone:
            is_user_exist = await sync_to_async(
                CustomUser.objects.filter(Q(username=username) | Q(phone_number=phone_number)).exists
            )()

        if is_user_exist:
            print("2.1) 🥶is_user_exist is True")
            raise ValidationError(
                {"detail": "An account already exists with this credentials"}
            )

        # TODO create code and temporary token and save to redis
        code = "".join([str(random.randint(0, 9)) for _ in range(4)])
        temporary_user_token = uuid4().hex

        extended_register_data = {
            temporary_user_token: temporary_user_token,
            code: code,
            **data,
        }
        print(f"1.2) 📝extended_register_data >> {extended_register_data}")

        try:
            json_extended_register_data = json.dumps(extended_register_data)
            await cache.aset(temporary_user_token, json_extended_register_data, 60 * 20)
        except Exception as e:
            print(f"🥶error in validate {e}")
            raise ValidationError(
                {"detail": "An error occurred while saving credentials to cache."}
            )

        # TODO send email or sms
        send_email_or_sms.delay(
            auth_type=auth_type,
            email_subject=f"Hi {username}, You have successfully registered.",
            email_message=f"Thanks for registration, Hurry up! Here is your code: {code}",
            email=email,
            phone_number=phone_number,
        )

        return {"temporary_user_token": temporary_user_token}


class VerificationSerializer(Serializer):
    code = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    async def validate(self, data):
        is_user_exist = False
        code = data.get("code")

        if code is None or len(code) != 4:
            raise ValidationError({"error": "Please provide a 4-digit verification code."})

        temporary_user_token = get_temporary_user_token(self.request)
        extended_register_data = await get_extended_register_data(temporary_user_token, for_verify=True)
        print("1.0) 📝temporary_user_token >> ", temporary_user_token)
        print("1.1) 📝extended_register_data >> ", extended_register_data)

        # TODO check for existence of code and temporary user token
        if not all(key in extended_register_data for key in [temporary_user_token, code]):
            raise ValidationError(
                {"detail": "The code has expired or you provided an invalid code.", "code": "invalid_code"}
            )

        # TODO gathering registration data
        username = extended_register_data.get("username")
        auth_type = extended_register_data.get("auth_type")
        email = extended_register_data.get("email")
        phone_number = extended_register_data.get("phone_number")
        password = extended_register_data.get("password")

        registration_data = {
            "username": username, "auth_type": auth_type, "password": password,
            "email": email, "phone_number": phone_number,
        }

        # TODO check for existing user
        if registration_data.get("auth_type") == AuthType.email:
            is_user_exist = await sync_to_async(
                CustomUser.objects.filter(Q(username=username) | Q(email=email)).exists
            )()
        elif registration_data.get("auth_type") == AuthType.phone:
            is_user_exist = await sync_to_async(
                CustomUser.objects.filter(Q(username=username) | Q(phone_number=phone_number)).exists
            )()

        if is_user_exist:
            raise ValidationError(
                {"detail": "Your account already has been verified. Please login."}
            )

        registered_user = await CustomUser.objects.acreate(**registration_data)

        user_token = await sync_to_async(registered_user.get_user_tokens)()
        user_data = await CustomUserSerializer(registered_user).adata

        return {**user_data, **user_token}


class LoginSerializer(Serializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    async def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username is None:
            raise ValidationError({"detail": "Username must be provided.", "code": "username_not_provided"})
        if password is None:
            raise ValidationError({"detail": "Password must be provided.", "code": "password_not_provided"})

        user = await sync_to_async(authenticate)(self.request, username=username, password=password)
        if user is None:
            raise ValidationError({"detail": "User not found.", "code": "user_not_found"})

        user_token = await sync_to_async(user.get_user_tokens)()
        user_data = await CustomUserSerializer(user).adata

        return {**user_data, **user_token}


class CustomUserSerializer(ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)
    followers = serializers.SerializerMethodField(read_only=True)
    followings = serializers.SerializerMethodField(read_only=True)
    profession_name = serializers.SerializerMethodField()
    banner_color = serializers.CharField(read_only=True)
    profession = serializers.PrimaryKeyRelatedField(queryset=Profession.objects.all(), write_only=True)
    avatar = serializers.ImageField()
    banner = serializers.ImageField()

    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "followers", "followings", "avatar", "banner", "banner_color",
            "first_name", "last_name", "email", "phone_number", "date_of_birth", "date_joined",
            "gender", "location", "bio", "telegram_username", "instagram_username", "twitter_username",
            "youtube_channel", "github_username", "profession", "profession_name", "education", "password",
        ]

    @staticmethod
    def get_followers(obj):
        return obj.follower.count()

    @staticmethod
    def get_followings(obj):
        return obj.following.count()

    @staticmethod
    def get_profession_name(obj):
        if obj.profession:
            return obj.profession.name
        return None

    async def validate_user_data(
            self, username, first_name, last_name, email, phone_number, avatar, banner, profession,
            password, date_of_birth, gender, education, bio,
            telegram_username, instagram_username, twitter_username, youtube_channel, github_username
    ):
        validation_errors = {
            "username": CustomSerializerValidator.validate_username(username),
            "names": CustomSerializerValidator.validate_names(first_name, last_name),
            "password": CustomSerializerValidator.validate_password(password),
            "email_or_phone": CustomSerializerValidator.validate_email_and_phone_number(email, phone_number),
            "date": CustomSerializerValidator.validate_date_of_birth(date_of_birth),
            "gender": CustomSerializerValidator.validate_gender(gender),
            "profession": await CustomSerializerValidator.validate_profession(profession),
            "avatar_or_banner": await CustomSerializerValidator.validate_avatar_and_banner(avatar, banner),
            "education": CustomSerializerValidator.validate_education(education),
            "bio": CustomSerializerValidator.validate_bio(bio),
            "user_exists": await CustomSerializerValidator.validate_to_user_exists(
                username, email, phone_number, first_name, last_name
            ),
            "social": CustomSerializerValidator.validate_social_media(
                telegram_username, instagram_username, twitter_username, youtube_channel, github_username
            )
        }

        for key, error in validation_errors.items():
            if error:
                print(f"error >> {error}, type >> {type(error)}")
                raise ValidationError({"detail": error})

    async def validate(self, data):
        print(f"validate data >> {data}")
        username = data.get("username")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        password = data.get("password")
        email = data.get("email")
        phone_number = data.get("phone_number")
        profession = data.get("profession")
        date_of_birth = data.get("date_of_birth")
        gender = data.get("gender")
        avatar = data.get("avatar")
        banner = data.get("banner")
        education = data.get("education")
        bio = data.get("bio")
        telegram_username = data.get("telegram_username")
        instagram_username = data.get("instagram_username")
        twitter_username = data.get("twitter_username")
        youtube_channel = data.get("youtube_channel")
        github_username = data.get("github_username")

        # TODO validation function
        await self.validate_user_data(
            username, first_name, last_name, email, phone_number, avatar, banner, profession,
            password, date_of_birth, gender, education, bio,
            telegram_username, instagram_username, twitter_username, youtube_channel, github_username
        )

        return data

    async def aupdate(self, instance, validated_data):
        print(f"aupdate validated_data >> {validated_data}")
        for key, value in (await validated_data).items():
            print(f"aupdate key >> {key}: value >> {value}")
            setattr(instance, key, value)
        await sync_to_async(instance.save)()
        print(f"aupdate instance.username >> {instance.username}")
        print(f"aupdate instance.avatar >> {instance.avatar}")
        print(f"aupdate instance.avatar.url >> {instance.avatar.url}")
        return instance

    async def asave(self):
        print(f"asave self.validated_data >> {self.validated_data}")
        print(f"asave self.instance >> {self.instance}")
        return await self.aupdate(self.instance, self.validated_data)

    async def ato_representation(self, instance):
        return await sync_to_async(super().to_representation)(instance)


class TabSerializer(ModelSerializer):
    id = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Tab
        fields = ["id", "name"]

    def validate(self, data):
        owner = self.context.get("owner")
        name = data.get("name")
        print(f"data >{data}\n owner > {owner}\n name > {name}")
        if not owner:
            raise ValidationError("Tab owner must provided")
        elif not name:
            raise ValidationError("Tab name must provided")
        elif Tab.objects.filter(owner=owner, name=name).exists():
            raise ValidationError("Tab already exists")
        data["owner"] = owner
        return data

    def create(self, validated_data):
        new_tab = Tab.objects.create(**validated_data)
        print(f"new_note_category >> {new_tab}")
        return new_tab

    def update(self, instance, validated_data):
        print(f"validated_data >> {validated_data}")
        instance.name = validated_data.get("name", instance.name)
        instance.tab_sequence_number = validated_data.get(
            "tab_sequence_number", instance.tab_sequence_number
        )
        instance.save()
        return instance


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    owner = CustomUserSerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Tab.objects.all(), required=False
    )

    class Meta:
        model = Note
        fields = [
            "id",
            "owner",
            "body",
            "category",
        ]

    def validate(self, data):
        owner = self.context.get("owner")
        body = data.get("body")
        category = data.get("category")
        print(
            f"owner >> {owner}\n body >> {body}\n category >> {category}, data >> {data}"
        )
        if not owner:
            raise ValidationError("Owner of the note must be provided")
        elif not body:
            raise ValidationError("Note body must be provided")
        elif Note.objects.filter(owner=owner, body=body).exists():
            raise ValidationError("Note already exist")
        elif category and not Tab.objects.filter(id=category.id, owner=owner).exists():
            raise ValidationError(
                "Category must belongs to owner of the note"
            )
        data["owner"] = owner
        return data

    def create(self, validated_data):
        created_note = Note.objects.create(**validated_data)
        print(f"created_note >> {created_note}")
        return created_note

    def update(self, instance, validated_data):
        print(f"validated_data >> {validated_data}")
        instance.body = validated_data.get("body", instance.body)
        instance.category = validated_data.get("category", instance.category)
        instance.isPinned = validated_data.get("isPinned", instance.isPinned)
        instance.note_sequence_number = validated_data.get(
            "note_sequence_number", instance.note_sequence_number
        )
        instance.save()
        return instance


class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ["id", "name"]


class CustomUsersSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "phone_number"]
