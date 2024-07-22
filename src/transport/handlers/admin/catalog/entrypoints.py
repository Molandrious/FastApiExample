from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from base_objects.models import IdResponse
from services import CatalogService
from services.catalog.models import CreateProductDTO, ProductDetailed, Publication
from services.file_manager.service import FileManagerService
from transport.depends import get_catalog_service, get_file_manager_service
from transport.handlers.admin.catalog.schemas import (
    CreateCategoryRequestSchema,
    CreateProductSchema,
    CreatePublicationRequestSchema,
    GetCategoryListResponseSchema,
    GetFilterGroupsResponseSchema,
    GetProductListResponseSchema,
    GetPublicationListResponseSchema,
)
from transport.handlers.admin.catalog.utils import parce_create_product_form
from transport.middlewares.logging_middleware import FastAPILoggingRoute

admin_router = APIRouter(
    prefix='/admin',
    tags=['admin'],
    route_class=FastAPILoggingRoute,
)


@admin_router.post(
    '/product',
    status_code=status.HTTP_201_CREATED,
    response_model=IdResponse,
)
async def create_product_entrypoint(
    file_manager_service: Annotated[FileManagerService, Depends(get_file_manager_service)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    product: Annotated[CreateProductSchema, Depends(parce_create_product_form)],
) -> IdResponse:
    product_id = await catalog_service.create_product(
        CreateProductDTO.model_validate(product),
    )

    attachments = await file_manager_service.upload_product_images(
        product_id=product_id,
        images=product.images,
    )

    await catalog_service.add_attachments_to_product(attachments)

    return IdResponse(id=product_id)


@admin_router.get(
    '/product',
    status_code=status.HTTP_200_OK,
    response_model=ProductDetailed,
)
async def get_product_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    id: UUID,
) -> ProductDetailed:
    return await catalog_service.get_product(product_id=id)


@admin_router.get(
    '/product-list',
    status_code=status.HTTP_200_OK,
    response_model=GetProductListResponseSchema,
)
async def get_product_list_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> GetProductListResponseSchema:
    a = GetProductListResponseSchema(items=await catalog_service.get_product_list())
    return a


@admin_router.get(
    '/filter-groups',
    status_code=status.HTTP_200_OK,
    response_model=GetFilterGroupsResponseSchema,
)
async def get_filter_groups_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    category_name: str,
):
    return GetFilterGroupsResponseSchema(items=await catalog_service.get_filter_groups_by_category(category_name))


@admin_router.post(
    '/publication',
    status_code=status.HTTP_201_CREATED,
    response_model=IdResponse,
)
async def create_publication_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    publication: CreatePublicationRequestSchema,
) -> IdResponse:
    result = await catalog_service.create_publication(
        link=publication.link,
        delivery_cost_included=publication.delivery_cost_included,
        catalog_items=publication.items,
    )

    return IdResponse(id=result)


@admin_router.get(
    '/publication',
    status_code=status.HTTP_200_OK,
    response_model=Publication,
)
async def get_publication_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    id: UUID,
) -> Publication:
    return await catalog_service.get_publication(publication_id=id)


@admin_router.get(
    '/publication-list',
    status_code=status.HTTP_200_OK,
    response_model=GetPublicationListResponseSchema,
)
async def get_publication_list_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> GetPublicationListResponseSchema:
    return GetPublicationListResponseSchema(items=await catalog_service.get_publications())


@admin_router.get(
    '/category-list',
    status_code=status.HTTP_200_OK,
    response_model=GetCategoryListResponseSchema,
)
async def get_categories_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> GetCategoryListResponseSchema:
    return GetCategoryListResponseSchema(items=await catalog_service.get_categories())


@admin_router.post(
    '/category',
    status_code=status.HTTP_201_CREATED,
    response_model=IdResponse,
)
async def create_category_entrypoint(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    category: CreateCategoryRequestSchema,
) -> IdResponse:
    return IdResponse(
        id=await catalog_service.create_category(
            title=category.title,
            link=category.link,
        )
    )
