from httpx import HTTPStatusError
from loguru import logger

from integrations.integration_client_utils import BaseApiClient
from settings import Settings


class OryKratosClient(BaseApiClient):
    _base_url = Settings().env.ory_kratos.public_url

    async def get_session(self, cookies: dict) -> dict | None:
        response = await self.get(
            url='/sessions/whoami',
            cookies=cookies,
        )

        try:
            response.raise_for_status()
        except HTTPStatusError as ex:
            logger.error(ex)
            return None

        logger.debug(response.json())
        return response.json()
