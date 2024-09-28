from datetime import timedelta
from django.utils import timezone
import re
from django.contrib.auth import get_user_model
from shared_app.utils import cache_get_or_set
from users_app.models import Profession, Gender

CustomUser = get_user_model()


class CustomSerializerValidator:
    # TODO error messages
    username_exists_error = "The username already in use."
    email_exists_error = "The email already in use."
    phone_number_exists_error = "The phone number already in use."
    full_name_exists_error = "The full name already in use."
    username_regex_error = ("Username must start with a lowercase letter and can only contain lowercase letters, "
                            "digits,and underscores. It should be 4-20 characters long.")
    password_regex_error = ("Password must contain at least one lowercase letter, and one digit. "
                            "It should be 8-20 characters long.")
    f_and_l_name_same_error = "The first and last name must be different."
    names_too_short_or_too_long_error = "The first and last name must be 4-20 characters long."
    email_invalid_error = "The email is invalid."
    phone_number_invalid_error = "The phone number is invalid."
    birth_date_invalid_error = "The birthdate must be between 7 years ago and 100 years ago."
    gender_invalid_error = "The gender must be male or female."
    profession_id_invalid_error = "The profession id is invalid."
    education_too_long_error = "The education must be 200 characters or less."
    bio_too_long_error = "The bio must be 200 characters or less."
    telegram_username_too_long_error = "The telegram username must be 50 characters or less."
    instagram_username_too_long_error = "The instagram username must be 50 characters or less."
    twitter_username_too_long_error = "The twitter username must be 50 characters or less."
    youtube_channel_too_long_error = "The youtube channel must be 50 characters or less."
    github_username_too_long_error = "The github username must be 50 characters or less."

    # TODO regex
    username_regex = r'^[a-z][a-z0-9_]{3,19}$'
    password_regex = r'^(?!.*(\d)\1{2})(?!.*([a-zA-Z])\2{2})(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{8,20}$'
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_number_regex = r'^\+[1-9]\d{1,14}$'

    @classmethod
    def validate_username(cls, username):
        if username and not re.match(cls.username_regex, username):
            return cls.username_regex_error

        return False

    @classmethod
    def validate_password(cls, password):
        if password and not re.match(cls.password_regex, password):
            return cls.password_regex_error

        return False

    @classmethod
    async def validate_to_user_exists(cls, username, email=None, phone_number=None, first_name=None, last_name=None):
        cached_users_list = await cache_get_or_set(
            key="users_list",
            callable_queryset=lambda: list(CustomUser.objects.values_list(
                "username", "email", "phone_number", "first_name", "last_name",
            )),
            expire_time=60 * 60 * 3,
        )

        print("cached_users_list >>>", cached_users_list, type(cached_users_list))

        # TODO Extract relevant information while filtering out None values
        usernames = [user[0] for user in cached_users_list]
        emails = [user[1] for user in cached_users_list if user[1] is not None]
        phone_numbers = [user[2] for user in cached_users_list if user[2] is not None]
        name_pairs = [
            (user[3].lower(), user[4].lower())
            for user in cached_users_list if user[3] and user[4]
        ]

        if username in usernames:
            return cls.username_exists_error
        if email and email in emails:
            return cls.email_exists_error
        if phone_number and phone_number in phone_numbers:
            return cls.phone_number_exists_error

        if first_name and last_name and (first_name.lower(), last_name.lower()) in name_pairs:
            return cls.full_name_exists_error

        return False

    @classmethod
    def validate_names(cls, first_name, last_name):
        if first_name and last_name and first_name.lower() == last_name.lower():
            return cls.f_and_l_name_same_error

        is_valid_first_name = first_name and (len(first_name) < 4 or len(first_name) > 20)
        is_valid_last_name = last_name and (len(last_name) < 4 or len(last_name) > 20)
        if is_valid_first_name or is_valid_last_name:
            return cls.names_too_short_or_too_long_error

        return False

    @classmethod
    def validate_email_and_phone_number(cls, email, phone_number):
        if email and re.match(cls.email_regex, email):
            return cls.email_invalid_error

        if phone_number and re.match(cls.phone_number_regex, phone_number):
            return cls.phone_number_invalid_error

        return False

    @classmethod
    def validate_date_of_birth(cls, date_of_birth):
        hundred_years_ago = timezone.now().date() - timedelta(days=365 * 100)
        seven_years_ago = timezone.now().date() - timedelta(days=365 * 7)
        if date_of_birth and not (hundred_years_ago < date_of_birth < seven_years_ago):
            return cls.birth_date_invalid_error

        return False

    @classmethod
    def validate_gender(cls, gender):
        if gender and gender not in [Gender.male, Gender.female]:
            return cls.gender_invalid_error

        return False

    @classmethod
    async def validate_profession(cls, profession_id):
        cached_professions_list = await cache_get_or_set(
            key="professions_list",
            callable_queryset=lambda: list(Profession.objects.values_list("id", "name")),
            expire_time=60 * 60 * 3,
        )

        print("cached_professions_list >>>", cached_professions_list, type(cached_professions_list))

        if profession_id and cached_professions_list:
            profession_ids = [prof[0] for prof in cached_professions_list]
            print("profession_ids >>>", profession_ids, type(profession_ids))

            if profession_id not in profession_ids:
                return cls.profession_id_invalid_error

        return False

    @classmethod
    async def validate_avatar_and_banner(cls, avatar, banner):
        print(f"avatar: {avatar}, type: {type(avatar)}\n banner: {banner} type: {type(banner)}")
        if avatar:
            print(f"avatar: {avatar.__dict__}")
        if banner:
            print(f"banner: {banner.__dict__}")

        return False

    @classmethod
    def validate_education(cls, education):
        if education and len(education) > 200:
            return cls.education_too_long_error

        return False

    @classmethod
    def validate_bio(cls, bio):
        if bio and len(bio) > 200:
            return cls.bio_too_long_error

        return False

    @classmethod
    def validate_social_media(cls, telegram_username, instagram_username, twitter_username, youtube_channel,
                              github_username):
        if telegram_username and len(telegram_username) > 50:
            return cls.telegram_username_too_long_error

        if instagram_username and len(instagram_username) > 50:
            return cls.instagram_username_too_long_error

        if twitter_username and len(twitter_username) > 50:
            return cls.twitter_username_too_long_error

        if youtube_channel and len(youtube_channel) > 50:
            return cls.youtube_channel_too_long_error

        if github_username and len(github_username) > 50:
            return cls.github_username_too_long_error

        return False
