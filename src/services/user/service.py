from uuid import UUID

from constants import MAX_CART_ITEM_QUANTITY
from database.models import UserFavoritesORM
from database.repositories import UserRepository
from services.catalog.models import ShortCheckoutItem
from services.user.errors import CartItemQuantityInvalidError
from services.user.models import (
    CartItem,
    UserItems,
)
from utils import USER_IDENTITY_CTX


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
    ) -> None:
        self.user_repository = user_repository

    async def get_user_items(self, user_id: UUID) -> UserItems:
        cart_items = await self.user_repository.get_user_cart_items(user_id=user_id)
        favorites = await self.user_repository.get_user_favorite_items(user_id=user_id)
        return UserItems(
            cart=[CartItem(id=item.id, quantity=item.quantity) for item in cart_items],
            favorites=[item.catalog_item_id for item in favorites],
        )

    async def change_cart_item_quantity(
        self,
        item_id: UUID,
        session_cart: dict,
        available_items: int,
        *,
        is_increment_action: bool,
    ) -> None:
        if user := USER_IDENTITY_CTX.get():
            cart_quantity = await self.user_repository.get_cart_item_quantity(
                item_id=item_id,
                user_id=user.id,
            )
        else:
            cart_quantity = session_cart.get(item_id, 0)

        new_cart_quantity = cart_quantity + 1 if is_increment_action else cart_quantity - 1

        if not (0 < new_cart_quantity <= max(available_items, MAX_CART_ITEM_QUANTITY)):
            raise CartItemQuantityInvalidError

        if not session_cart:
            await self.user_repository.update_cart_item_quantity(
                item_id=item_id,
                user_id=user.id,
                new_quantity=new_cart_quantity,
            )
        else:
            session_cart[item_id] = new_cart_quantity

    async def add_item_to_cart(self, user_id: UUID, item_id: UUID) -> None:
        await self.user_repository.add_item_to_cart(user_id=user_id, item_id=item_id)

    async def remove_items_from_cart(self, user_id: UUID, item_ids: list[UUID]) -> None:
        await self.user_repository.remove_items_from_cart(user_id=user_id, item_ids=item_ids)

    async def update_cart_items(self, user_id: UUID, updated_cart_items: list[ShortCheckoutItem]) -> None:
        cart_items = await self.user_repository.get_user_cart_items(user_id=user_id)

        for item in updated_cart_items:
            for db_cart_item in cart_items:
                if db_cart_item.id == item.id:
                    db_cart_item.quantity = item.quantity
                    break

    async def add_favorite_item(self, catalog_item_id: UUID, user_id: UUID) -> None:
        await self.user_repository.create(
            UserFavoritesORM(
                user_id=user_id,
                catalog_item_id=catalog_item_id,
            ),
        )

    async def remove_favorite_item(self, catalog_item_id: UUID, user_id: UUID) -> None:
        await self.user_repository.remove_favorite_item(
            catalog_item_id=catalog_item_id,
            user_id=user_id,
        )
