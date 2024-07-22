from enum import StrEnum

SELF_PICKUP_ADDRESS = 'г. Москва, м. Красные Ворота, ул. Новая Басманная, д.12, с2 (выход из метро №2)'
SELF_PICKUP_IDENTIFIER = 'Самовывоз'


class DeliveryService(StrEnum):
    CDEK = 'CDEK'
    SELF_PICKUP = 'SELF_PICKUP'


class InvoiceStatus(StrEnum):
    UNPAID = 'UNPAID'
    WAITING = 'WAITING'
    PAID = 'PAID'
    CANCELED = 'CANCELED'


class OrderStatus(StrEnum):
    UNPAID = 'UNPAID'
    ACCEPTED = 'ACCEPTED'
    ASSEMBLY = 'ASSEMBLY'
    DELIVERY = 'DELIVERY'
    FINISHED = 'FINISHED'
    CANCELED = 'CANCELED'


class InvoiceType(StrEnum):
    INITIAL = 'INITIAL'
    CREDIT = 'CREDIT'
    SHIPPING_FOREIGN = 'SHIPPING_FOREIGN'
    SHIPPING_LOCAL = 'SHIPPING_LOCAL'


PAYMENT_TO_INVOICE_STATUS_MAPPING = {
    'AUTHORIZED': InvoiceStatus.WAITING,
    'CONFIRMED': InvoiceStatus.PAID,
}

INVOICE_TO_ORDER_STATUS_MAPPING = {
    InvoiceStatus.PAID: OrderStatus.ACCEPTED,
}

DELIVERY_TRACKING_LINK_MAPPING = {
    DeliveryService.CDEK.value: 'https://www.cdek.ru/ru/tracking/?order_id=',
}
