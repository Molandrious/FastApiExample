import pendulum

from integrations.integration_client_utils import BaseApiClient
from integrations.tinkoff.models import InitPaymentResponse
from settings import Settings


class CdekClient(BaseApiClient):
    _base_url = Settings().env.cdek_integration.url
    _logging = False

    def __init__(self):
        super().__init__()
        self.password = Settings().env.cdek_integration.password
        self.client_id = Settings().env.cdek_integration.client_id
        self.token_expires = None

    async def _set_auth_token(self) -> None:
        response = await self.post(
            url='/oauth/token',
            params={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.password,
            },
        )
        response.raise_for_status()

        self.token = response.json()['access_token']
        self.token_expires = pendulum.now().add(seconds=int(response.json()['expires_in']) - 100)

    def _is_token_valid(self) -> bool:
        return self.token_expires and self.token_expires > pendulum.now()

    async def get_token(self) -> str:
        if self._is_token_valid():
            return self.token

        await self._set_auth_token()
        return self.token

    async def get_offices(self, params: dict) -> InitPaymentResponse:
        response = await self.get(
            '/deliverypoints',
            headers={'Authorization': f'Bearer {await self.get_token()}'},
            params=params,
            timeout=30.0,
        )

        return response.json()

    async def calculate(self, data: dict) -> InitPaymentResponse:
        response = await self.post(
            '/calculator/tarifflist',
            headers={'Authorization': f'Bearer {await self.get_token()}'},
            json=data,
        )

        return response.json()
