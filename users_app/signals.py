import shutil
from asgiref.sync import sync_to_async
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from shared_app.utils import get_dominant_color_async, get_s3_client_async
from users_app.models import CustomUser
from pathlib import Path
from django.conf import settings
from asyncio import to_thread


BASE_DIR = Path(__file__).resolve().parent.parent


async def update_banner_color(instance):
    """Helper function to update banner color."""
    if settings.STORAGE_DESTINATION == "s3":
        object_key = instance.banner.name
        dominant_color = get_dominant_color_async(object_key=object_key)
        if dominant_color:
            instance.banner_color = dominant_color
    elif settings.STORAGE_DESTINATION == "local":
        banner_path = instance.banner.path
        dominant_color = await get_dominant_color_async(path=banner_path)
        if dominant_color:
            instance.banner_color = dominant_color
            await sync_to_async(instance.save)()


@receiver(post_save, sender=CustomUser)
async def set_banner_color_when_user_created(sender, instance, created, **kwargs):
    if created or "banner" in instance.get_dirty_fields():
        await update_banner_color(instance)


@receiver(post_delete, sender=CustomUser)
async def delete_user_avatar_and_banner(sender, instance, **kwargs):
    if settings.STORAGE_DESTINATION == "s3":
        s3, aws_storage_bucket_name = await get_s3_client_async()
        user_folder_key = f"{settings.MEDIA_LOCATION}/users/user_{instance.username}/"

        objects_to_delete = await to_thread(
            s3.list_objects_v2(Bucket=aws_storage_bucket_name, Prefix=user_folder_key)
        )
        if "Contents" in objects_to_delete:
            delete_keys = [{"Key": obj["Key"]} for obj in objects_to_delete["Contents"]]
            await to_thread(
                s3.delete_objects(Bucket=aws_storage_bucket_name, Delete={"Objects": delete_keys})
            )

    elif settings.STORAGE_DESTINATION == "local":
        # instance.avatar.name >> defaults/default_avatar.png
        # instance.avatar.url >> media/defaults/default_avatar.png
        # instance.banner.path >> /home/kamronbek/Desktop/backend_1/media/defaults/default_banner.png
        user_folder_path = Path(instance.avatar.path).parent
        if Path(user_folder_path).exists() and instance.avatar.name != "defaults/default_avatar.png":
            try:
                await to_thread(shutil.rmtree, user_folder_path, ignore_errors=True, onerror=None)
            except Exception as e:
                print(f"Error deleting user folder: {e}")
