from integrations.cdek.client import CdekClient
from integrations.s3.client import S3Client
from integrations.tinkoff.client import TinkoffClient
from settings import Settings


async def get_s3_client() -> S3Client:
    yield S3Client(config=Settings().env.s3)


async def get_tinkoff_client() -> TinkoffClient:
    yield TinkoffClient()


async def get_cdek_client() -> CdekClient:
    yield CdekClient()
