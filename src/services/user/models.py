from uuid import UUID

from pydantic import Field

from base_objects.models import SGBaseModel


class CartItem(SGBaseModel):
    id: UUID
    quantity: int


class UserItems(SGBaseModel):
    cart: list[CartItem] = Field(default_factory=list)
    favorites: list[UUID] = Field(default_factory=list)
    tracked: list[UUID] = Field(default_factory=list)
