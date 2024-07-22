from operator import or_
from uuid import UUID

from pendulum import Date
from psycopg2.errorcodes import CHECK_VIOLATION
from sqlalchemy import select
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_dbapi
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from base_objects.models import SGBaseModel
from database.models import (
    AttachmentORM,
    CatalogItemORM,
    FilterGroupORM,
    ProductCategoryORM,
    ProductORM,
    PublicationORM,
)
from database.repositories.base import ISqlAlchemyRepository
from errors.base import BaseError, ExpectedError


class CatalogItemNotFoundError(ExpectedError):
    status_code: int = 404
    message: str = 'Товар не найден'


class CatalogItemOutOfStockError(BaseError):
    status_code = 400
    message = 'Отсутствует необходимое кол-во товаров'


class CreditPart(SGBaseModel):
    sum: int
    deadline: Date


class CatalogItemCheckoutDataDTO(SGBaseModel):
    id: UUID
    total: int | None
    ordered: int
    price: int
    preorder_id: UUID | None = None
    title: str
    credit_parts: list[CreditPart] | None

    @property
    def available(self) -> int | None:
        return (self.total - self.ordered) if self.total else None


class CatalogRepository(ISqlAlchemyRepository):
    async def get_publications(
        self,
    ) -> list[PublicationORM]:
        result = await self.session.scalars(select(PublicationORM))
        return list(result.all())

    async def get_publication(self, publication_id: UUID) -> PublicationORM:
        return await self.session.get(PublicationORM(), publication_id)

    async def get_available_catalog_item_ids(self) -> list[UUID]:
        query = select(CatalogItemORM.id).where(
            CatalogItemORM.is_active,
            or_(
                CatalogItemORM.quantity > CatalogItemORM.ordered_quantity,
                not CatalogItemORM.quantity,
            ),
        )

        result = await self.session.scalars(query)
        return list(result.all())

    async def get_filter_groups_by_category(self, category_link: str) -> list[FilterGroupORM]:
        result = await self.session.scalars(
            select(FilterGroupORM).where(FilterGroupORM.product_category.has(link=category_link))
        )
        return list(result.all())

    async def create_product_with_filters(self, product: ProductORM) -> UUID:
        product = await self.session.merge(product)
        return product.id

    async def get_category_by_link(self, category_link: str) -> ProductCategoryORM:
        result = await self.session.scalars(select(ProductCategoryORM).where(ProductCategoryORM.link == category_link))
        return result.one_or_none()

    async def add_attachments_to_product(self, attachments: list[AttachmentORM]) -> None:
        self.session.add_all(attachments)

    async def create_publication(self, publication: PublicationORM) -> UUID:
        self.session.add(publication)
        return publication.id

    async def get_catalog_item_quantity(self, item_id: UUID) -> CatalogItemCheckoutDataDTO | None:
        query = select(
            CatalogItemORM.quantity,
            CatalogItemORM.ordered_quantity,
        ).where(
            CatalogItemORM.id == item_id,
        )

        if not (result := (await self.session.execute(query)).one_or_none()):
            raise CatalogItemNotFoundError

        return CatalogItemCheckoutDataDTO(id=item_id, total=result[0], ordered=result[1]) if result else None

    async def get_catalog_items_checkout_data(self, item_ids: list[UUID]) -> dict[UUID, CatalogItemCheckoutDataDTO]:
        query = select(CatalogItemORM).where(
            CatalogItemORM.is_active,
            CatalogItemORM.id.in_(item_ids),
        )

        result = await self.session.scalars(query)

        if len(result_items := list(result)) != len(item_ids):
            raise CatalogItemNotFoundError

        return {
            item.id: CatalogItemCheckoutDataDTO(
                id=item.id,
                total=item.quantity,
                ordered=item.ordered_quantity,
                preorder_id=item.publication_info.preorder_id,
                price=item.price,
                title=item.product.title,
                credit_parts=(
                    [CreditPart(sum=int(part.sum), deadline=str(part.deadline)) for part in item.credit_plan.parts]
                    if item.credit_plan
                    else None
                ),
            )
            for item in result_items
        }

    async def get_all_products(self) -> list[ProductORM]:
        result = await self.session.scalars(select(ProductORM))
        return list(result.all())

    async def get_product(self, product_id: UUID) -> ProductORM | None:
        result = await self.session.scalars(
            select(ProductORM)
            .where(ProductORM.id == product_id)
            .options(
                selectinload(ProductORM.catalog_items),
            )
        )
        return result.one_or_none()

    async def increase_catalog_items_ordered_quantity(self, items_to_update: dict[UUID, int]) -> None:
        catalog_items = await self.session.scalars(
            select(CatalogItemORM).where(CatalogItemORM.id.in_(items_to_update.keys())).with_for_update()
        )

        for item in catalog_items:
            item.ordered_quantity = item.ordered_quantity + items_to_update[item.id]

        try:
            await self.session.flush()
        except IntegrityError as ex:
            if isinstance(ex.orig, AsyncAdapt_asyncpg_dbapi.IntegrityError) and ex.orig.pgcode == CHECK_VIOLATION:
                raise CatalogItemOutOfStockError from ex
            raise
