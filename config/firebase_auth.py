import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
from environ import Env
import asyncio
from functools import partial


BASE_DIR = Path(__file__).resolve().parent.parent
env = Env()
# Todo: remove when using docker env_file
Env.read_env(BASE_DIR / ".env")

firebase_credentials = credentials.Certificate({
    "type": env.str("TYPE", default=""),
    "project_id": env.str("FIREBASE_PROJECT_ID", default=""),
    "private_key_id": env.str("FIREBASE_PRIVATE_KEY_ID", default=""),
    "private_key": env.str("FIREBASE_PRIVATE_KEY", default="", multiline=True),
    "client_email": env.str("FIREBASE_CLIENT_EMAIL", default=""),
    "client_id": env.str("FIREBASE_CLIENT_ID", default=""),
    "auth_uri": env.str("AUTH_URI", default=""),
    "token_uri": env.str("TOKEN_URI", default=""),
    "auth_provider_x509_cert_url": env.str("AUTH_PROVIDER_X509_CERT_URI", default=""),
    "client_x509_cert_url": env.str("FIREBASE_CLIENT_CERT_URL", default="")
})
firebase_admin.initialize_app(firebase_credentials)


async def custom_firebase_validation(firebase_id_token):
    """
   This function receives id token sent by Firebase and
   validate the id token then check if the user exist on
   Firebase or not, if exist it returns display_name, email,
   phone_number, photo_url else False
   """
    try:
        decoded_token = await asyncio.to_thread(partial(auth.verify_id_token, firebase_id_token))
        print(f"DECODED_TOKEN: {decoded_token}")
        uid = decoded_token["uid"]
        try:
            user = await asyncio.to_thread(partial(auth.get_user, uid))
            print(f"USER: {user}")
            return {
                "display_name": user.display_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "photo_url": user.photo_url,
            }
        except auth.UserNotFoundError:
            print("user not exist")
            return None
    except auth.ExpiredIdTokenError:
        print("invalid token")
        return None
