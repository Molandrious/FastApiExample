from uuid import UUID

from pydantic import Field

from base_objects.models import SGBaseModel
from services.catalog.models import CatalogItemQuantity, ShortCheckoutItem
from services.order.models import Delivery


class CreateOrderRequestSchema(SGBaseModel):
    delivery_data: Delivery | None = Field(default=None)
    credit_ids: list[UUID] = Field(default_factory=list)


class CreateOrderResponseSchema(SGBaseModel):
    payment_link: str


class MakeCheckoutRequestSchema(SGBaseModel):
    items: list[CatalogItemQuantity]


class GetCheckoutDataResponseSchema(SGBaseModel):
    items: list[ShortCheckoutItem]
