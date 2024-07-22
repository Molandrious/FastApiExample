from datetime import date
from uuid import UUID

from pydantic import Field

from database.constants import DeliveryCostType
from base_objects.models import BaseEntity, SGBaseModel


class FilterDTO(SGBaseModel):
    id: UUID | None = None
    value: str


class FilterGroup(SGBaseModel):
    id: UUID | None = None
    title: str
    filters: list[FilterDTO]


class PreorderBaseInfoDTO(SGBaseModel):
    title: str
    expected_arrival: date | None


class CreditPaymentPart(SGBaseModel):
    sum: int
    deadline: str


class CreditInfo(SGBaseModel):
    payments: list[CreditPaymentPart]


class PublishedItemShortDTO(SGBaseModel):
    id: UUID
    title: str
    link: str
    price: int
    index: int | None = None
    is_active: bool
    is_available: bool
    is_preorder: bool
    credit_info: CreditInfo | None = None
    filter_groups: list[FilterGroup]


class PublishedItemCardDTO(PublishedItemShortDTO):
    image_url: str


class PublishedItemDTO(PublishedItemShortDTO):
    description: str | None
    image_urls: list[str]


class CatalogItemDTO(SGBaseModel):
    category_link: str
    preorder_info: PreorderBaseInfoDTO | None
    variations: list[PublishedItemDTO]


class PhysicalPropertiesDTO(SGBaseModel):
    length: float | None = None
    height: float | None = None
    width: float | None = None
    weight: float | None = None


class CreateProductDTO(SGBaseModel):
    title: str
    category_link: str
    description: str | None = None
    physical_properties: PhysicalPropertiesDTO | None = None
    filter_groups: list[FilterGroup] = Field(default_factory=list)


#############################


class CatalogItemQuantity(SGBaseModel):
    id: UUID
    quantity: int


class ShortCheckoutItem(SGBaseModel):
    id: UUID
    quantity: int


class AvailableCheckoutItem(ShortCheckoutItem):
    preorder_id: UUID | None = None
    price: int
    title: str
    credit_parts: list[CreditPaymentPart] | None

    @property
    def amount_converted(self):
        return self.price * self.quantity * 100

    @property
    def price_converted(self):
        return self.price * 100


class CheckoutData(SGBaseModel):
    available_items: list[AvailableCheckoutItem] = Field(default_factory=list)
    adjusted_items: list[ShortCheckoutItem] = Field(default_factory=list)


class CatalogCategory(BaseEntity):
    title: str
    link: str


class CreateCatalogItemDTO(SGBaseModel):
    product_id: UUID
    price: int
    quantity: int | None = None
    discount: int | None = None
    credit_info: CreditInfo | None = None


class PhysicalProperties(SGBaseModel):
    width: float
    height: float
    length: float
    weight: float = Field(alias='mass')


class Preorder(BaseEntity):
    title: str
    expected_arrival: date | None
    status: str


class Product(BaseEntity):
    title: str
    description: str | None
    physical_properties: PhysicalProperties | None
    category: CatalogCategory
    filter_groups: list[FilterGroup]
    images: list[str]


class ProductDetailed(Product):
    is_published: bool


class CatalogItem(BaseEntity):
    price: int
    quantity: int | None = None
    is_active: bool
    discount: int | None = None
    index: int | None = Field(alias='variationIndex')
    credit_info: CreditInfo | None = None
    product: Product


class Publication(BaseEntity):
    link: str
    preorder: Preorder | None
    delivery_cost_included: DeliveryCostType | None = None
    items: list[CatalogItem]
