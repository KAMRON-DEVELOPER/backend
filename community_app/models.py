from django.core.exceptions import ValidationError
from django.db import models
# from config.storage_backends import PrivateMediaStorage
from shared_app.models import BaseModel
from django.contrib.auth import get_user_model
from dirtyfields import DirtyFieldsMixin


CustomUser = get_user_model()


def user_directory_path(instance, filename):
    # file will be uploaded to private/user_<username>/media_messages/<filename>
    return "user_{}/media_messages/{}".format(instance.user.username, filename)


class PostCategory(BaseModel):
    """category_name"""
    category_name = models.CharField(max_length=50, unique=True)


class Tag(models.Model):
    """tag_name"""
    tag_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tag_name


class Post(BaseModel):
    """title, content, author, category, tags"""
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(PostCategory, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, related_name="posts")

    def clean(self):
        super().clean()
        if self.tags.count() > 5:
            raise ValidationError('You cannot add more than 5 tags to post')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        words = self.title.split()
        if len(words) > 2:
            return ' '.join(words[:2])
        return self.title


class PostComment(BaseModel):
    """post, user, comment, image, parent"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="post_comments")
    comment = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='comment_gifs/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        words = self.comment.split()
        if len(words) > 2:
            return f"Comment by {self.user} on {self.post.title}"
        return self.comment


class PostLike(BaseModel):
    """post, user"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user} likes {self.post.title}"


class CommentLike(BaseModel):
    """comment, user"""
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user} likes {self.comment}"


class RoomType(models.TextChoices):
    chat = "chat", "chat"
    group = "group", "group"


class Room(BaseModel):
    """name, room_type, members, add_member(user), remove_member(user)"""
    name = models.CharField(max_length=30, unique=True, null=True, blank=True)
    room_type = models.CharField(max_length=5, choices=RoomType.choices, default=RoomType.chat)
    members = models.ManyToManyField(CustomUser, related_name='rooms')

    def __str__(self):
        return f"Room: {self.name}"

    def add_member(self, user):
        if self.room_type == RoomType.group:
            print(f"user: {user}")
        # self.members.add(user)

    def remove_member(self, user):
        if self.room_type == RoomType.group:
            print(f"user: {user}")
        # self.members.remove(user)


class RoomMessage(BaseModel, DirtyFieldsMixin):
    """room, user, text_message, media_message"""
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name="messages", on_delete=models.CASCADE)
    text_message = models.TextField(null=True, blank=True)
    media_message = models.FileField(upload_to=user_directory_path, null=True, blank=True)

    def __str__(self):
        return f"Message by {self.user} in {self.room.name}"

    def clean(self):
        super().clean()
        if not self.text_message and not self.media_message:
            raise ValidationError("Either text or media_message must be provided.")
