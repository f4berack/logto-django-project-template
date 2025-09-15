import os
import hvac
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from logto import LogtoClient, LogtoConfig, Storage
from asgiref.sync import sync_to_async

client = hvac.Client(
    url='http://127.0.0.1:8200',
    token='dev-only-token',
)

logto_secret = client.secrets.kv.read_secret_version(path='logto_secret')

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
            endpoint=logto_secret['data']['data']['endpoint'],
            appId=logto_secret['data']['data']['client_id'],
            appSecret=logto_secret['data']['data']['client_secret']
        ),
        storage=SessionStorage(session),
    )


class SigninView(View):
    async def get(self, request):
        client = get_logto_client(request.session)
        redirect_uri = logto_secret['data']['data']['redirect_uri']
        sign_in_url = await client.signIn(redirectUri=redirect_uri)
        
        return HttpResponseRedirect(sign_in_url)


class CallbackView(View):
    async def get(self, request):
        client = get_logto_client(request.session)
        absolute_uri = request.build_absolute_uri()
        callback_uri = logto_secret['data']['data']['callback_uri']
        
        try:
            await client.handleSignInCallback(absolute_uri)
            return HttpResponseRedirect(callback_uri)
        except Exception as e:
            return HttpResponse("Error: " + str(e)) 

