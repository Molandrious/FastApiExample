from __future__ import annotations

from typing import ClassVar
from uuid import UUID, uuid4

from pendulum import Date, DateTime
from pydantic import Json
from pydantic.alias_generators import to_snake
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime as SQLAlchemyDateTime,
    ForeignKey,
    Index,
    JSON,
    MetaData,
    Text,
    UniqueConstraint,
    Date as SQLAlchemyDate,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, relationship

from database.constants import CONSTRAINT_NAMING_CONVENTIONS
from integrations.sql_alchemy.utils import force_default_column_arguments_before_commit

force_default_column_arguments_before_commit()


class BaseDeclarative(DeclarativeBase):
    metadata = MetaData(naming_convention=CONSTRAINT_NAMING_CONVENTIONS)

    type_annotation_map: ClassVar[dict[type, type]] = {
        DateTime: SQLAlchemyDateTime(timezone=True),
        Date: SQLAlchemyDate,
        Json: JSON,
        dict: JSON,
    }


class BaseORM(AsyncAttrs, BaseDeclarative):
    __abstract__ = True

    @classmethod
    @declared_attr.directive
    def __tablename__(cls):
        return to_snake(cls.__name__.rstrip('ORM'))

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
        default=uuid4,
        sort_order=-3,
    )

    created_at: Mapped[DateTime] = mapped_column(
        insert_default=DateTime.now,
        nullable=False,
        sort_order=-2,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        insert_default=DateTime.now,
        onupdate=DateTime.now,
        nullable=True,
        sort_order=-1,
    )

    def __repr__(self):
        return str(self.__dict__)


class ProductCategoryORM(BaseORM):
    link: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=False)

    filter_groups: Mapped[list[FilterGroupORM]] = relationship(
        back_populates='product_category',
    )
    products: Mapped[list[ProductORM]] = relationship(
        back_populates='category',
    )


class AttachmentORM(BaseORM):
    product_id: Mapped[UUID] = mapped_column(ForeignKey('product.id'), nullable=False, index=True)
    type: Mapped[str] = mapped_column(nullable=False)
    index: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)


class ProductORM(BaseORM):
    category_id: Mapped[UUID] = mapped_column(ForeignKey('product_category.id'), nullable=False)

    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    physical_properties: Mapped[Json] = mapped_column(nullable=True)

    filters: Mapped[list[FilterORM]] = relationship(
        secondary='product_filter',
        lazy='selectin',
        back_populates='products',
        cascade='merge',
    )
    category: Mapped[ProductCategoryORM] = relationship(back_populates='products', lazy='selectin')
    attachments: Mapped[list[AttachmentORM]] = relationship(
        lazy='selectin',
        order_by=(AttachmentORM.product_id, AttachmentORM.type, AttachmentORM.index),
    )
    catalog_items: Mapped[list[CatalogItemORM]] = relationship(back_populates='product', lazy='selectin')


class ProductFilterORM(BaseORM):
    filter_id: Mapped[UUID] = mapped_column(ForeignKey('filter.id'), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey('product.id'), nullable=False)


class FilterORM(BaseORM):
    filter_group_id: Mapped[UUID] = mapped_column(ForeignKey('filter_group.id'), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    group: Mapped[FilterGroupORM] = relationship(
        back_populates='filters',
        lazy='selectin',
        cascade='merge',
    )
    products: Mapped[list[ProductORM]] = relationship(
        secondary='product_filter',
        back_populates='filters',
    )
    # product_associations: Mapped[list[ProductFilter]] = relationship(back_populates='filter')


class FilterGroupORM(BaseORM):
    product_category_id: Mapped[UUID] = mapped_column(ForeignKey('product_category.id'), nullable=False, index=True)

    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)

    product_category: Mapped[ProductCategoryORM] = relationship(back_populates='filter_groups', lazy='selectin')
    filters: Mapped[list[FilterORM]] = relationship(back_populates='group', lazy='selectin')


class PreorderORM(BaseORM):
    title: Mapped[str] = mapped_column(nullable=False)
    prefix: Mapped[str] = mapped_column(nullable=True)
    expected_arrival: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False)


class PublicationORM(BaseORM):
    preorder_id: Mapped[UUID | None] = mapped_column(ForeignKey('preorder.id'), nullable=True, index=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    link: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    delivery_cost_included: Mapped[str | None] = mapped_column(nullable=True)

    preorder: Mapped[PreorderORM] = relationship(lazy='selectin')
    items: Mapped[list[CatalogItemORM]] = relationship(
        back_populates='publication_info',
        lazy='selectin',
    )


class CreditPartORM(BaseORM):
    credit_plan_id: Mapped[UUID] = mapped_column(ForeignKey('credit_plan.id'), nullable=False, index=True)
    sum: Mapped[int] = mapped_column(nullable=False)
    deadline: Mapped[Date] = mapped_column(nullable=False)


class CreditPlanORM(BaseORM):
    title: Mapped[str] = mapped_column(nullable=False, unique=True)

    catalog_items: Mapped[list[CatalogItemORM]] = relationship(back_populates='credit_plan', lazy='noload')
    parts: Mapped[list[CreditPartORM]] = relationship(lazy='selectin')


class CatalogItemORM(BaseORM):
    __table_args__ = (CheckConstraint('quantity IS NULL OR ordered_quantity <= quantity', name='quantity_limit'),)

    publication_id: Mapped[UUID] = mapped_column(ForeignKey('publication.id'), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey('product.id'), nullable=False)
    credit_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey('credit_plan.id'), nullable=True)

    price: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    index: Mapped[int | None] = mapped_column(nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=True)
    ordered_quantity: Mapped[int] = mapped_column(nullable=False, default=0)

    credit_plan: Mapped[CreditPlanORM] = relationship(back_populates='catalog_items', lazy='selectin')
    product: Mapped[ProductORM] = relationship(back_populates='catalog_items', lazy='selectin')
    publication_info: Mapped[PublicationORM] = relationship(back_populates='items', lazy='selectin')


#
# class Discount(BaseORM):
#     title: Mapped[str] = mapped_column(nullable=False)
#     sum: Mapped[int] = mapped_column(nullable=False)
#     is_active: Mapped[bool] = mapped_column(nullable=False)
#     start_at: Mapped[DateTime] = mapped_column(nullable=False)
#     end_at: Mapped[DateTime] = mapped_column(nullable=True)
#
#     discount_products = relationship("DiscountProduct")


class OrderORM(BaseORM):
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    preorder_id: Mapped[UUID] = mapped_column(ForeignKey('preorder.id'), nullable=True)
    delivery_id: Mapped[UUID | None] = mapped_column(ForeignKey('delivery.id'), nullable=True)
    status: Mapped[str] = mapped_column(nullable=False)

    order_items: Mapped[list[OrderItemORM]] = relationship(
        'OrderItemORM',
        lazy='selectin',
    )
    invoices: Mapped[list[InvoiceORM]] = relationship(
        'InvoiceORM',
        back_populates='order',
        lazy='selectin',
    )
    delivery: Mapped[DeliveryORM | None] = relationship(
        'DeliveryORM',
        lazy='selectin',
    )
    preorder: Mapped[PreorderORM] = relationship(
        'PreorderORM',
        lazy='selectin',
    )


class OrderItemORM(BaseORM):
    item_id: Mapped[UUID] = mapped_column(ForeignKey('catalog_item.id'))
    order_id: Mapped[UUID] = mapped_column(ForeignKey('order.id'), index=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    by_credit: Mapped[bool] = mapped_column(nullable=False)

    invoices: Mapped[list[InvoiceORM]] = relationship(
        'InvoiceORM',
        back_populates='item',
        lazy='selectin',
    )

    info: Mapped[CatalogItemORM] = relationship(
        'CatalogItemORM',
        lazy='selectin',
    )


class PaymentORM(BaseORM):
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey('invoice.id'), nullable=False, index=True)

    url: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    external_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    invoice: Mapped[InvoiceORM] = relationship(
        'InvoiceORM',
        back_populates='payments',
        lazy='selectin',
    )


class InvoiceORM(BaseORM):
    order_id: Mapped[UUID] = mapped_column(ForeignKey('order.id'), nullable=False, index=True)
    order_item_id: Mapped[UUID | None] = mapped_column(ForeignKey('order_item.id'), nullable=True, index=True)

    credit_part_index: Mapped[int] = mapped_column(nullable=True, default=None)
    title: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)

    payments: Mapped[list[PaymentORM]] = relationship(
        'PaymentORM',
        back_populates='invoice',
        lazy='selectin',
    )
    order: Mapped[OrderORM] = relationship(
        'OrderORM',
        back_populates='invoices',
        lazy='selectin',
    )
    item: Mapped[OrderItemORM | None] = relationship(
        'OrderItemORM',
        back_populates='invoices',
        lazy='selectin',
    )


class DeliveryORM(BaseORM):
    service: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    address_identifier: Mapped[str | None] = mapped_column(nullable=True, default=None)
    recipient_name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    recipient_phone: Mapped[str | None] = mapped_column(nullable=True, default=None)
    track_code: Mapped[str | None] = mapped_column(nullable=True, default=None)


class CartItemORM(BaseORM):
    __table_args__ = (
        UniqueConstraint('user_id', 'item_id'),
        Index('idx_cart_item', 'item_id', 'user_id', unique=True),
        CheckConstraint('quantity > 0', name='positive_cart_item_quantity_check'),
    )

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    item_id: Mapped[UUID] = mapped_column(ForeignKey('catalog_item.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)

    info: Mapped[CatalogItemORM] = relationship(lazy='selectin')

class FaqEntriesORM(BaseORM):
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    index: Mapped[int] = mapped_column(nullable=False)


class UserFavoritesORM(BaseORM):
    user_id: Mapped[UUID] = mapped_column(nullable=False)
    catalog_item_id: Mapped[UUID] = mapped_column(ForeignKey('catalog_item.id'), nullable=False)
