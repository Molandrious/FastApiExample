from enum import StrEnum


CONSTRAINT_NAMING_CONVENTIONS = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class InvoiceStatus(StrEnum):
    CREATED = 'CREATED'
    PAID = 'PAID'
    EXPIRED = 'EXPIRED'
    CANCELED = 'CANCELED'
    FAILED = 'FAILED'
    PENDING = 'PENDING'


class AttachmentType(StrEnum):
    IMAGE = 'IMAGE'


class PublicationType(StrEnum):
    STOCK = 'STOCK'
    PREORDER = 'PREORDER'


class DeliveryCostType(StrEnum):
    FULL = 'FULL'
    FOREIGN = 'FOREIGN'
    NOT = 'NOT'
