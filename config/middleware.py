from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from asyncio import to_thread
from functools import partial


async def get_user(token):
    # Instantiate JWTAuthentication to use its methods
    jwt_auth = JWTAuthentication()

    try:
        # Get validated token from raw token
        validated_token = to_thread(jwt_auth.get_validated_token, token)

        # Get the user associated with the validated token
        user = await to_thread(partial(jwt_auth.get_user, validated_token))

        # print("validated_token: ", validated_token)
        # print("user: ", user)

        return user
    except InvalidToken or TokenError:
        user = AnonymousUser()
    return user


class CustomTokenAuthMiddleWare:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers_list_bytes = scope["headers"]  # [..., (b'authorization', b'Bearer eyJ343aer...)]
        # headers_dict_bytes = dict(headers_list_bytes)
        headers_dict_str = {k.decode('utf-8'): v.decode('utf-8') for k, v in headers_list_bytes}
        auth_bearer_token = headers_dict_str.get(b"authorization")  # b'Bearer eyJ343aer...

        if auth_bearer_token is None:
            scope["user"] = AnonymousUser()
            return await self.app(scope, receive, send)

        token_type, token = auth_bearer_token.split()

        user = await get_user(token)
        scope["user"] = user
        return await self.app(scope, receive, send)
