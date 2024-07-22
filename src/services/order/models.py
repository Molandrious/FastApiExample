from uuid import UUID

from pendulum import DateTime

from base_objects.models import SGBaseModel
from database.repositories.catalog import CreditPart
from services.order.constants import DeliveryService, InvoiceType, OrderStatus


class Recipient(SGBaseModel):
    full_name: str
    phone: str


class DeliveryPoint(SGBaseModel):
    address: str
    code: str


class Delivery(SGBaseModel):
    recipient: Recipient
    service: DeliveryService
    point: DeliveryPoint | None


class Tracking(SGBaseModel):
    code: str
    link: str


class OutputDeliveryData(Delivery):
    tracking: Tracking | None = None


class CreditInfo(SGBaseModel):
    title: str
    parts: list[CreditPart]


class Invoice(SGBaseModel):
    id: UUID
    credit_part_index: int | None
    amount: int
    type: InvoiceType
    is_paid: bool


class Credit(SGBaseModel):
    invoice: Invoice | None
    paid_parts: int
    payments: list[CreditPart]


class OrderItem(SGBaseModel):
    id: UUID
    title: str
    image: str
    quantity: int
    sum: int
    credit: Credit | None


class PreorderInfo(SGBaseModel):
    id: UUID
    title: str
    status: str
    expected_arrival: str | None = None


class Order(SGBaseModel):
    id: UUID
    created_at: DateTime
    status: OrderStatus
    delivery: OutputDeliveryData | None
    tracking: Tracking | None = None
    preorder: PreorderInfo | None
    items: list[OrderItem]
    invoices: list[Invoice]
