import os
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from logto import LogtoClient, LogtoConfig, Storage
from asgiref.sync import sync_to_async

class SessionStorage(Storage):
    def __init__(self, session):
        self.session = session

    async def get(self, key: str):
        return await sync_to_async(self.session.get)(key, "")

    async def set(self, key: str, value: str | None) -> None:
        await sync_to_async(self.session.__setitem__)(key, value)

    async def delete(self, key: str) -> None:
        await sync_to_async(self.session.__delitem__)(key)


def get_logto_client(session):
    return LogtoClient(
        LogtoConfig(
            endpoint=os.environ.get("LOGTO_API_ENDPOINT"),
            appId=os.environ.get("LOGTO_API_CLIENT_ID"),
            appSecret=os.environ.get("LOGTO_API_SECRET")
        ),
        storage=SessionStorage(session),
    )


class SigninView(View):
    async def get(self, request):
        client = get_logto_client(request.session)
        redirect_uri = os.environ.get("LOGTO_API_REDIRECT_URI")
        sign_in_url = await client.signIn(redirectUri=redirect_uri)
        
        return HttpResponseRedirect(sign_in_url)


class CallbackView(View):
    async def get(self, request):
        client = get_logto_client(request.session)
        absolute_uri = request.build_absolute_uri()
        callback_uri = os.environ.get("LOGTO_API_CALLBACK_URI")
        
        try:
            await client.handleSignInCallback(absolute_uri)
            return HttpResponseRedirect(callback_uri)
        except Exception as e:
            return HttpResponse("Error: " + str(e)) 

