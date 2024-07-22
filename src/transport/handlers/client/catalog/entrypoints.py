from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from starlette import status

from integrations.redis.utils import query_params_key_builder
from services import CatalogService
from transport.depends import get_catalog_service
from transport.handlers.client.catalog.schemas import (
    GetPublicationsResponseSchema,
)
from transport.middlewares.logging_middleware import FastAPILoggingRoute

market_router = APIRouter(tags=['market'], prefix='/market', route_class=FastAPILoggingRoute)


@market_router.get(
    path='/catalog',
    summary='Get full catalog',
    status_code=status.HTTP_200_OK,
    response_model=GetPublicationsResponseSchema,
)
@cache(expire=3600, namespace='catalog', key_builder=query_params_key_builder)
async def get_catalog_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> GetPublicationsResponseSchema:
    return GetPublicationsResponseSchema(items=await catalog_service.get_publications())


@market_router.get(
    path='/availability/catalog',
    summary='Get catalog items availability',
    status_code=status.HTTP_200_OK,
)
async def get_catalog_availability_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> list[UUID]:
    return await catalog_service.get_available_catalog_item_ids()


@market_router.get(
    path='/availability/publication',
    summary='Get catalog items availability for publication',
    status_code=status.HTTP_200_OK,
)
async def get_publication_items_availability_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],  # noqa
    link: str,  # noqa
) -> list[UUID]:
    raise NotImplementedError


@market_router.get(
    path='/suggested-items',
    status_code=status.HTTP_200_OK,
)
async def get_suggested_items():
    return {'items': []}
