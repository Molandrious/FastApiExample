from loguru import logger

from integrations.integration_client_utils import BaseApiClient
from integrations.tinkoff.errors import InitPaymentError
from integrations.tinkoff.models import InitPaymentRequest, InitPaymentResponse
from settings import Settings


class TinkoffClient(BaseApiClient):
    _base_url = Settings().env.tinkoff_integration.url

    async def init_payment(self, data: InitPaymentRequest) -> InitPaymentResponse:
        data.token = data.generate_token()
        response = await self.post(
            '/Init',
            json=data.model_dump(exclude_none=True, by_alias=True),
        )

        response.raise_for_status()

        if (response_json := response.json()) and response_json.get('ErrorCode') != '0':
            logger.error(response.json())
            raise InitPaymentError(message=response_json.get('Details'))

        return InitPaymentResponse.model_validate(response.json())
