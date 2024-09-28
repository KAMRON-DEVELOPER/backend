from dirtyfields import DirtyFieldsMixin
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from shared_app.models import BaseModel


def user_directory_path(instance, filename):
    # file will be uploaded to user_<username>/<filename>
    return "users/user_{}/{}".format(instance.username, filename)


class AuthType(models.TextChoices):
    email = "email", "Email"
    phone = "phone", "Phone"


class Gender(models.TextChoices):
    male = "male", "Male"
    female = "female", "Female"


class Country(models.TextChoices):
    tashkent = "Tashkent", "Tashkent"


class Profession(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser, BaseModel, DirtyFieldsMixin):
    """username, first_name, last_name, email, bio, location, phone_number, avatar, banner, banner_color,
    date_of_birth, auth_status, gender, auth_type, telegram_username, instagram_username, twitter_username,
    youtube_channel, github_username, profession, education"""
    username = models.CharField(unique=True, null=True, blank=True, max_length=50)
    bio = models.TextField(null=True, blank=True)
    location = models.CharField(choices=Country.choices, null=True, blank=True, max_length=50)
    email = models.EmailField(unique=True, null=True, blank=True, max_length=50)
    phone_number = models.CharField(unique=True, null=True, blank=True, max_length=50)
    banner_color = models.CharField(max_length=7, default="#000000", null=True, blank=True)
    date_of_birth = models.DateField(editable=True, null=True, blank=True)
    gender = models.CharField(choices=Gender.choices, null=True, blank=True, max_length=6)
    auth_type = models.CharField(choices=AuthType.choices, default=AuthType.email, max_length=5)
    telegram_username = models.CharField(null=True, blank=True, max_length=100)
    instagram_username = models.CharField(null=True, blank=True, max_length=100)
    twitter_username = models.CharField(null=True, blank=True, max_length=100)
    youtube_channel = models.CharField(null=True, blank=True, max_length=100)
    github_username = models.CharField(null=True, blank=True, max_length=100)
    education = models.CharField(null=True, blank=True, max_length=50)
    avatar = models.ImageField(upload_to=user_directory_path, default="defaults/default_avatar.png")
    banner = models.ImageField(upload_to=user_directory_path, default="defaults/default_banner.png")
    profession = models.OneToOneField(
        Profession,
        related_name="users",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        max_length=50,
    )

    def __str__(self):
        return self.username

    def hashing_password(self):
        if not self.password.startswith("pbkdf2_sha256"):
            self.set_password(self.password)

    def get_user_tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"access_token": str(refresh.access_token), "refresh_token": str(refresh)}

    def save(self, *args, **kwargs):
        self.hashing_password()
        super(CustomUser, self).save(*args, **kwargs)


class Follow(BaseModel):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="follower")
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="follower_following_unique"),
        ]

    def __str__(self):
        return f"{self.follower} followed to {self.following}"

    def save(self, *args, **kwargs):
        if self.follower == self.following:
            raise ValidationError("You cannot follow yourself")
        super().save(*args, **kwargs)


class Tab(BaseModel):
    """owner, name"""
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tabs")
    name = models.CharField(max_length=20)

    def __str__(self):
        return f"'{self.name}' tab belong to {self.owner}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="tab_owner_name_unique"),
        ]


class Note(BaseModel):
    """owner, body, category"""
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notes", null=True,)
    body = models.TextField()
    category = models.ForeignKey(Tab, on_delete=models.CASCADE, related_name="notes", null=True, blank=True)

    def __str__(self):
        return f"'{self.body[:10]}' note belongs to {self.owner}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "body"], name="owner_body_unique"),
        ]
