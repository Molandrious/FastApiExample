from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from database.models import CartItemORM, UserFavoritesORM
from database.repositories.base import ISqlAlchemyRepository
from errors.base import ExpectedError


class CartItemNotFoundError(ExpectedError):
    status_code: int = 404
    message: str = 'Товар не найден'


class UserRepository(ISqlAlchemyRepository):
    async def get_user_cart_items(
        self,
        user_id: UUID,
    ) -> list[CartItemORM]:
        stmt = select(CartItemORM).where(CartItemORM.user_id == user_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def add_item_to_cart(
        self,
        user_id: UUID,
        item_id: UUID,
    ) -> None:
        stmt = insert(CartItemORM).values(user_id=user_id, item_id=item_id, quantity=1).on_conflict_do_nothing()
        await self.session.execute(stmt)

    async def remove_items_from_cart(
        self,
        user_id: UUID,
        item_ids: list[UUID],
    ) -> None:
        stmt = delete(CartItemORM).where(CartItemORM.user_id == user_id).where(CartItemORM.item_id.in_(item_ids))
        await self.session.execute(stmt)

    async def get_cart_item_quantity(
        self,
        item_id: UUID,
        user_id: UUID,
    ) -> int:
        result = (
            await self.session.execute(
                select(CartItemORM.quantity).where(
                    CartItemORM.item_id == item_id,
                    CartItemORM.user_id == user_id,
                ),
            )
        ).one_or_none()

        if not result:
            raise CartItemNotFoundError

        return result[0]

    async def update_cart_item_quantity(
        self,
        item_id: UUID,
        user_id: UUID,
        new_quantity: int,
    ) -> None:
        await self.session.execute(
            update(CartItemORM)
            .where(
                CartItemORM.item_id == item_id,
                CartItemORM.user_id == user_id,
            )
            .values(quantity=new_quantity)
        )

    async def get_user_favorite_items(
        self,
        user_id: UUID,
    ) -> list[UserFavoritesORM]:
        stmt = select(UserFavoritesORM).where(UserFavoritesORM.user_id == user_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def remove_favorite_item(self, catalog_item_id: UUID, user_id: UUID) -> None:
        stmt = delete(UserFavoritesORM).where(
            UserFavoritesORM.user_id == user_id,
            UserFavoritesORM.catalog_item_id == catalog_item_id,
        )

        await self.session.execute(stmt)
