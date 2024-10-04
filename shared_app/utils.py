from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.core.files.base import ContentFile
from modern_colorthief import get_color
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import boto3
from botocore.config import Config
from django.conf import settings
import random
import string
from django.contrib.auth.hashers import make_password
from users_app.models import CustomUser
import requests
from asyncio import to_thread
from functools import partial
import json
from django.core.files.storage import default_storage


async def get_s3_client_async():
    try:
        aws_storage_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        aws_s3_region_name = settings.AWS_S3_REGION_NAME

        boto_config = Config(region_name=aws_s3_region_name, signature_version="s3v4")

        s3 = boto3.client(
            service_name="s3",
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
            config=boto_config,
        )
        return [s3, aws_storage_bucket_name]
    except Exception as e:
        print(f"🥶 error in get_boto3_client: {e}")


# TODO UTILITIES
async def get_dominant_color_async(path=None, object_key=None, image_url=None):
    print(f"PATH >> {path}, OBJECT_KEY >> {object_key}, IMAGE_URL >> {image_url}")
    try:
        dominant_color = None
        if object_key or image_url:
            image_data = await download_image_async(object_key=object_key, image_url=image_url)
            image_bytes = await prepare_image_data_async(image_data=image_data)

            if image_bytes:
                dominant_color_rgb = await to_thread(get_color, image_bytes, quality=1)
                if dominant_color_rgb:
                    dominant_color = "#{:02x}{:02x}{:02x}".format(*dominant_color_rgb)
        elif path:
            print("path >>>", path)
            dominant_color_rgb = await to_thread(get_color, path, quality=1)
            print("dominant_color_rgb >>>", dominant_color_rgb)
            if dominant_color_rgb:
                dominant_color = "#{:02x}{:02x}{:02x}".format(*dominant_color_rgb)
        return dominant_color
    except Exception as e:
        print(f"Error getting dominant color: {e}")


async def download_image_async(object_key=None, image_url=None):
    print(f"🚧 OBJECT_KEY >> {object_key}, IMAGE_URL >> {image_url}")

    if object_key:
        try:
            s3, aws_storage_bucket_name = await get_s3_client_async()
            image_object = await to_thread(
                lambda: s3.get_object(
                    Bucket=aws_storage_bucket_name,
                    Key=f"{settings.MEDIA_LOCATION}/{object_key}",
                ),
            )
            image_data = BytesIO(image_object["Body"].read())
            return image_data
        except Exception as e:
            print(f"Error occurred while getting image: {e}")
            return None
    elif image_url:
        try:
            response = await to_thread(partial(requests.get, image_url))
            response.raise_for_status()
            image_data = BytesIO(response.content)
            print("🥳 image was downloaded >>>")
            return image_data
        except Exception as e:
            print(f"🥶 Error downloading image from URL: {e}")
            return None


async def prepare_image_data_async(image_data):
    try:
        pil_image = await to_thread(partial(Image.open, fp=image_data))
        pil_image.verify()  # verifying the image
        pil_image = await to_thread(partial(Image.open, fp=image_data))  # reopen the image

        if pil_image.mode in ("P", "1", "CMYK", "L", "LAB", "RGBA", "HSV", "F", "I"):
            pil_image = await to_thread(partial(pil_image.convert, mode="RGB"))  # remove alpha channel

        image_bytes = BytesIO()  # save the image again to RAM
        await to_thread(pil_image.save, image_bytes, format="PNG")
        image_bytes.seek(0)  # like proxy

        print("2) image was verified >>>")
        return image_bytes
    except UnidentifiedImageError:
        print("Error: The downloaded file is not a valid image.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


async def upload_image_to_storage(image_data, object_key):
    print(f"OBJECT_KEY >> {object_key}")
    if settings.STORAGE_DESTINATION == "s3":
        try:
            s3, aws_storage_bucket_name = await get_s3_client_async()

            await to_thread(
                s3.upload_fileobj,
                image_data, aws_storage_bucket_name, f"{settings.MEDIA_LOCATION}/{object_key}"
            )
            print(f"3) 🥳 Image successfully uploaded to S3 with key: {object_key}")
        except Exception as e:
            print(f"🥶 error uploading image to S3: {e}")
    else:
        image_data.seek(0)  # rewind the BytesIO
        default_storage.save(object_key, ContentFile(image_data.read()))
        print(f"3) 🥳 Image successfully saved to local storage with filename: {object_key}")


# TODO: generators
async def user_credential_generator(field, populated_field=None, generated_username=None):
    if field == "username" and populated_field is not None:
        return await generate_unique_username(populated_field)

    if field == "password":
        return await generate_password(length=8)

    if field == "avatar" and populated_field is not None:
        return await generate_avatar_url(populated_field, generated_username)


async def generate_unique_username(base_name):
    username = base_name.lower().replace(" ", "_")
    # TODO: caching usernames
    while await sync_to_async(CustomUser.objects.filter(username=username).exists)():
        username = f"{base_name.lower().replace(' ', '_')}_{random.randint(9, 9)}"
    print("4) ��� Unique username generated: ", username)
    return username


async def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(length))
    return make_password(password)


async def generate_avatar_url(image_url, generated_username):
    print(f"🚧 IMAGE_URL >> {image_url}, GENERATED_USERNAME >> {generated_username}")
    image_data = await download_image_async(image_url=image_url)
    if image_data:
        image_bytes = await prepare_image_data_async(image_data=image_data)
        if image_bytes:
            object_key = f"{generated_username}_avatar.jpg"  # generate filename
            print("4) ��� Object key generated: ", object_key)

            await upload_image_to_storage(image_bytes, f"users/{generated_username}/{object_key}")

            if settings.STORAGE_DESTINATION == "s3":
                generated_avatar_url = f"https://{settings.AWS_CUSTOM_DOMAIN}/media/users/{generated_username}/{object_key}"
            else:
                generated_avatar_url = f"{settings.MEDIA_URL}users/{generated_username}/{object_key}"
            print("5) ��� Avatar URL generated: ", generated_avatar_url)
            return generated_avatar_url


# TODO send email
def send_sms(phone_number):
    print(phone_number)


# TODO cache get or set
async def cache_get_or_set(key, callable_queryset, expire_time=60 * 15):
    setter_json = None
    try:
        getter_json = await cache.aget(key)
        if getter_json:
            print("getter_json >>>", getter_json, type(getter_json))
            try:
                getter_obj = json.loads(getter_json)
                return getter_obj
            except Exception as e:
                print(f"Error converting value from JSON: {e}")

        else:
            setter_raw = await sync_to_async(callable_queryset)()
            print("setter_raw >>>", setter_raw, type(setter_raw))
            try:
                if setter_raw:
                    setter_json = json.dumps(setter_raw)
                    print("setter_json >>>", setter_json, type(setter_json))
                try:
                    if setter_json:
                        await cache.aset(key, setter_json, expire_time)
                        return setter_raw
                except Exception as e:
                    print(f"Error caching value: {e}")
            except Exception as e:
                print(f"Error converting value to JSON: {e}")
    except Exception as e:
        print(f"Error caching value: {e}")


async def cache_get(key):
    try:
        getter_json = await cache.aget(key)
        if getter_json:
            print("getter_json >>>", getter_json, type(getter_json))
            try:
                getter_obj = json.loads(getter_json)
                print("getter_obj >>>", getter_obj, type(getter_obj))
                return getter_obj
            except Exception as e:
                print(f"Error converting value from JSON: {e}")
        else:
            return None
    except Exception as e:
        print(f"Error in cache_get value: {e}")


async def cache_set(key, value, expire_time=60 * 15):
    try:
        setter_json = json.dumps(value)

        if setter_json:
            print("setter_json >>>", setter_json, type(setter_json))
            try:
                await cache.aset(key, setter_json, expire_time)
                return True
            except Exception as e:
                print(f"Error caching value: {e}")
        else:
            return False
    except Exception as e:
        print(f"Error in cache_set value: {e}")
