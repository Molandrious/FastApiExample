from services.catalog.models import PreorderBaseInfoDTO, Publication, PublishedItemDTO
from base_objects.models import SGBaseModel


class GetCatalogItemResponse(SGBaseModel):
    category_link: str
    preorder_info: PreorderBaseInfoDTO | None
    variations: list[PublishedItemDTO]


class GetPublicationsResponseSchema(SGBaseModel):
    items: list[Publication]
