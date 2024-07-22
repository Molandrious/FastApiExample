from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from io import BytesIO

from aiobotocore.session import ClientCreatorContext, get_session

from settings import S3Settings


class S3Client:
    def __init__(
        self,
        config: S3Settings,
    ):
        self._config = config
        self._session = get_session()

    @property
    def base_url(self) -> str:
        return f'{self._config.endpoint_url}/{self._config.bucket_name}'

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[ClientCreatorContext, None]:
        async with self._session.create_client(
            **self._config.model_dump(by_alias=True, exclude={'bucket_name', 'public_url'})
        ) as client:
            yield client

    async def upload_file(self, file: BytesIO, key: str) -> None:
        async with self.get_client() as client:
            await client.put_object(
                Body=file,
                Bucket=self._config.bucket_name,
                Key=key,
            )
