from uuid import UUID

from fastapi import Form

from base_objects.models import SGBaseModel
from services.catalog.models import (
    CatalogCategory,
    CreateCatalogItemDTO,
    FilterGroup,
    PhysicalProperties,
    ProductDetailed,
    Publication,
)


class CreateProductSchema(SGBaseModel):
    title: str = Form()
    description: str | None = Form()
    category_link: str = Form(alias='category')
    physical_properties: PhysicalProperties = Form(alias='physicalProperties')
    filter_groups: list[FilterGroup] = Form(default_factory=list, alias='filterGroups')
    images: list[bytes]


class CreatePublicationRequestSchema(SGBaseModel):
    link: str
    items: list[CreateCatalogItemDTO]
    delivery_cost_included: bool | None = None
    preorder_id: UUID | None = None


class CreateCategoryRequestSchema(SGBaseModel):
    title: str
    link: str


class GetFilterGroupsResponseSchema(SGBaseModel):
    items: list[FilterGroup]


class GetProductListResponseSchema(SGBaseModel):
    items: list[ProductDetailed]


class GetPublicationListResponseSchema(SGBaseModel):
    items: list[Publication]


class GetCategoryListResponseSchema(SGBaseModel):
    items: list[CatalogCategory]
