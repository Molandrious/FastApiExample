from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import logger
from starlette.requests import Request

from integrations.cdek.client import CdekClient
from transport.depends.clients import get_cdek_client

cdek_router = APIRouter(tags=['cdek'])


@cdek_router.get('/cdek')
# @cache(expire=3600, namespace='cdek_offices', key_builder=query_params_key_builder)
async def get_cdek_offices(
    request: Request,
    cdek_client: Annotated[CdekClient, Depends(get_cdek_client)],
):
    logger.data(
        '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Get CDEK offices'  # noqa
    )
    return await cdek_client.get_offices(params=dict(request.query_params))


@cdek_router.post('/cdek')
async def make_calculate(
    request: Request,
    cdek_client: Annotated[CdekClient, Depends(get_cdek_client)],
):
    return await cdek_client.calculate(data=await request.json())
