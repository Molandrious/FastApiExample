from uuid import UUID, uuid4

from constants import MAX_CART_ITEM_QUANTITY
from database.constants import AttachmentType, DeliveryCostType, PublicationType
from database.models import (
    AttachmentORM,
    CatalogItemORM,
    FilterGroupORM,
    FilterORM,
    ProductCategoryORM,
    ProductORM,
    PublicationORM,
)
from database.repositories import CatalogRepository
from database.repositories.catalog import CatalogItemCheckoutDataDTO

from services.catalog.errors import IncorrectItemsSectionsError
from services.catalog.models import (
    AvailableCheckoutItem,
    CatalogCategory,
    CatalogItem,
    CatalogItemQuantity,
    CheckoutData,
    ShortCheckoutItem,
    CreateCatalogItemDTO,
    CreateProductDTO,
    CreditInfo,
    CreditPaymentPart,
    FilterDTO,
    FilterGroup,
    PhysicalProperties,
    Preorder,
    Product,
    ProductDetailed,
    Publication,
)
from services.catalog.utils import get_attachment_urls_by_type, prepare_filter_groups
from services.file_manager.models import Attachment


class CatalogService:
    def __init__(self, catalog_repository: CatalogRepository) -> None:
        self.catalog_repository = catalog_repository

    async def create_publication(
        self,
        link: str,
        catalog_items: list[CreateCatalogItemDTO],
        delivery_cost_included: DeliveryCostType | None = None,
    ) -> UUID:
        orm_catalog_items = [
            CatalogItemORM(
                product_id=item.product_id,
                price=item.price,
                is_active=True,
                quantity=item.quantity,
                index=index,
            )
            for index, item in enumerate(catalog_items)
        ]

        if len(orm_catalog_items) == 1:
            orm_catalog_items[0].index = None

        return await self.catalog_repository.create_publication(
            PublicationORM(
                link=link,
                type=PublicationType.STOCK.value,
                delivery_cost_included=delivery_cost_included,
                items=orm_catalog_items,
            ),
        )

    async def create_product(self, product_dto: CreateProductDTO) -> UUID:
        category = await self.catalog_repository.get_category_by_link(product_dto.category_link)

        filters = []
        for dto_filter_group in product_dto.filter_groups:
            db_filter_group = FilterGroupORM(
                id=dto_filter_group.id or uuid4(),
                title=dto_filter_group.title,
                product_category_id=category.id,
            )

            for filter in dto_filter_group.filters:
                filters.append(
                    FilterORM(
                        id=filter.id or uuid4(),
                        value=filter.value,
                        filter_group_id=dto_filter_group.id,
                        group=db_filter_group,
                    ),
                )

        product_id = await self.catalog_repository.create_product_with_filters(
            product=ProductORM(
                title=product_dto.title,
                description=product_dto.description,
                physical_properties=product_dto.physical_properties.model_dump(),
                filters=filters,
                category_id=category.id,
            )
        )

        return product_id

    async def get_product(self, product_id: UUID) -> ProductDetailed:
        product = await self.catalog_repository.get_product(product_id)
        return ProductDetailed(
            id=product.id,
            created_at=product.created_at,
            updated_at=product.updated_at,
            title=product.title,
            description=product.description,
            category=CatalogCategory.model_validate(product.category),
            images=get_attachment_urls_by_type(product.attachments, AttachmentType.IMAGE),
            physical_properties=PhysicalProperties.model_validate(product.physical_properties),
            filter_groups=prepare_filter_groups(product),
            is_published=bool(product.catalog_items),
        )

    async def get_product_list(self) -> list[ProductDetailed]:
        products = await self.catalog_repository.get_all_products()
        return [
            ProductDetailed(
                id=product.id,
                created_at=product.created_at,
                updated_at=product.updated_at,
                description=product.description,
                title=product.title,
                category=CatalogCategory.model_validate(product.category),
                images=get_attachment_urls_by_type(product.attachments, AttachmentType.IMAGE),
                physical_properties=(
                    PhysicalProperties.model_validate(product.physical_properties)
                    if product.physical_properties
                    else None
                ),
                filter_groups=prepare_filter_groups(product),
                is_published=bool(product.catalog_items),
            )
            for product in products
        ]

    async def get_publications(
        self,
    ) -> list[Publication]:
        publications = await self.catalog_repository.get_publications()

        prepared_publications = []
        for publication in publications:
            if not any(catalog_item.is_active for catalog_item in publication.items):
                continue

            prepared_catalog_items = []
            for catalog_item in publication.items:
                if not catalog_item.is_active:
                    continue

                prepared_catalog_items.append(
                    CatalogItem(
                        id=catalog_item.id,
                        created_at=catalog_item.created_at,
                        updated_at=catalog_item.updated_at,
                        price=catalog_item.price,
                        quantity=catalog_item.quantity,
                        is_active=catalog_item.is_active,
                        index=catalog_item.index,
                        credit_info=(
                            CreditInfo(
                                payments=(
                                    [
                                        CreditPaymentPart.model_validate(credit_part)
                                        for credit_part in catalog_item.credit_plan.parts
                                    ]
                                )
                            )
                            if catalog_item.credit_plan
                            else None
                        ),
                        product=Product(
                            id=catalog_item.product.id,
                            created_at=catalog_item.product.created_at,
                            updated_at=catalog_item.product.updated_at,
                            title=catalog_item.product.title,
                            description=catalog_item.product.description,
                            category=CatalogCategory.model_validate(catalog_item.product.category),
                            physical_properties=PhysicalProperties.model_validate(
                                catalog_item.product.physical_properties
                            ),
                            filter_groups=prepare_filter_groups(catalog_item.product),
                            images=get_attachment_urls_by_type(catalog_item.product.attachments, AttachmentType.IMAGE),
                        ),
                    )
                )

            prepared_publications.append(
                Publication(
                    id=publication.id,
                    created_at=publication.created_at,
                    updated_at=publication.updated_at,
                    link=publication.link,
                    preorder=Preorder.model_validate(publication.preorder) if publication.type == 'preorder' else None,
                    items=prepared_catalog_items,
                    delivery_cost_included=publication.delivery_cost_included,
                )
            )

        return prepared_publications

    async def get_publication(self, publication_id: UUID) -> Publication:
        publication = await self.catalog_repository.read(PublicationORM, publication_id)

        prepared_catalog_items = []
        for catalog_item in publication.items:
            if not catalog_item.is_active:
                continue

            prepared_catalog_items.append(
                CatalogItem(
                    id=catalog_item.id,
                    created_at=catalog_item.created_at,
                    updated_at=catalog_item.updated_at,
                    price=catalog_item.price,
                    quantity=catalog_item.quantity,
                    is_active=catalog_item.is_active,
                    index=catalog_item.variation_index,
                    credit_info=(
                        CreditInfo(
                            payments=(
                                [
                                    CreditPaymentPart.model_validate(credit_part)
                                    for credit_part in catalog_item.credit_plan.parts
                                ]
                            )
                        )
                        if catalog_item.credit_plan
                        else None
                    ),
                    product=Product(
                        id=catalog_item.product.id,
                        created_at=catalog_item.product.created_at,
                        updated_at=catalog_item.product.updated_at,
                        title=catalog_item.product.title,
                        description=catalog_item.product.description,
                        category=CatalogCategory.model_validate(catalog_item.product.category),
                        physical_properties=PhysicalProperties.model_validate(catalog_item.product.physical_properties),
                        filter_groups=prepare_filter_groups(catalog_item.product),
                        images=get_attachment_urls_by_type(catalog_item.product.attachments, AttachmentType.IMAGE),
                    ),
                )
            )

        return Publication(
            id=publication.id,
            created_at=publication.created_at,
            updated_at=publication.updated_at,
            link=publication.link,
            preorder=Preorder.model_validate(publication.preorder) if publication.type == 'preorder' else None,
            delivery_cost_included=publication.delivery_cost_included,
            items=prepared_catalog_items,
        )

    async def get_filter_groups_by_category(
        self,
        category_link: str,
    ) -> list[FilterGroup]:
        filter_groups = await self.catalog_repository.get_filter_groups_by_category(category_link=category_link)

        filters = []
        for item in filter_groups:
            filters.append(
                FilterGroup(
                    id=item.id,
                    title=item.title,
                    filters=sorted(
                        [FilterDTO.model_validate(filter) for filter in item.filters], key=lambda x: x.value
                    ),
                ),
            )

        return sorted(filters, key=lambda x: x.title)

    async def get_catalog_item_quantity(self, item_id: UUID) -> CatalogItemCheckoutDataDTO:
        return await self.catalog_repository.get_catalog_item_quantity(item_id=item_id)

    async def verify_checkout_data(self, checkout_items: list[CatalogItemQuantity]) -> CheckoutData:
        db_checkout_data = await self.catalog_repository.get_catalog_items_checkout_data(
            [item.id for item in checkout_items]
        )

        result = CheckoutData()

        first_item_preorder_id = next(iter(db_checkout_data.values())).preorder_id
        if not all(item.preorder_id == first_item_preorder_id for item in db_checkout_data.values()):
            raise IncorrectItemsSectionsError

        for item in checkout_items:
            db_item = db_checkout_data.get(item.id)

            if db_item.available is not None and item.quantity > db_item.available:
                db_data = min(db_item.available, MAX_CART_ITEM_QUANTITY)
                result.adjusted_items.append(ShortCheckoutItem(id=item.id, quantity=db_data))
            else:
                result.available_items.append(
                    AvailableCheckoutItem(
                        id=item.id,
                        quantity=item.quantity,
                        preorder_id=db_item.preorder_id,
                        price=db_item.price,
                        title=db_item.title,
                        credit_parts=db_item.credit_parts,
                    )
                )

        return result

    async def get_available_catalog_item_ids(self) -> list[UUID]:
        return await self.catalog_repository.get_available_catalog_item_ids()

    async def add_attachments_to_product(self, attachments: list[Attachment]) -> None:
        await self.catalog_repository.add_attachments_to_product(
            [
                AttachmentORM(
                    url=attachment.url,
                    type=attachment.type,
                    index=attachment.index,
                    product_id=attachment.product_id,
                )
                for attachment in attachments
            ]
        )

    async def reserve_catalog_items(self, items: list[ShortCheckoutItem]) -> None:
        await self.catalog_repository.increase_catalog_items_ordered_quantity(
            items_to_update={item.id: item.quantity for item in items}
        )

    async def get_categories(self) -> list[CatalogCategory]:
        return [
            CatalogCategory.model_validate(item) for item in await self.catalog_repository.read_all(ProductCategoryORM)
        ]

    async def create_category(self, title: str, link: str) -> UUID:
        return await self.catalog_repository.create(ProductCategoryORM(title=title, link=link))
