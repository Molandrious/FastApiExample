from uuid import UUID

import pendulum

from constants import HOURS_TILL_ORDER_EXPIRES
from database.constants import AttachmentType
from database.models import DeliveryORM, InvoiceORM, OrderItemORM, OrderORM, PaymentORM
from database.repositories.order import OrderRepository
from errors.auth import ForbiddenError
from integrations.ory_kratos.models import UserIdentity
from integrations.tinkoff.client import TinkoffClient
from integrations.tinkoff.models import InitPaymentRequest, PaymentStatusNotification, Receipt, ReceiptItem
from services.catalog.models import AvailableCheckoutItem
from services.catalog.utils import get_attachment_urls_by_type
from services.order.constants import (
    DELIVERY_TRACKING_LINK_MAPPING,
    INVOICE_TO_ORDER_STATUS_MAPPING,
    InvoiceStatus,
    InvoiceType,
    OrderStatus,
    PAYMENT_TO_INVOICE_STATUS_MAPPING,
)
from services.order.models import (
    Credit,
    CreditPart,
    Delivery,
    DeliveryPoint,
    Invoice,
    Order,
    OrderItem,
    PreorderInfo,
    Recipient,
    Tracking,
)
from services.order.utils import make_order_invoices_objects


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        tinkoff_client: TinkoffClient,
    ) -> None:
        self.order_repository = order_repository
        self.tinkoff_client = tinkoff_client

    async def create_order(
        self,
        user: UserIdentity,
        credit_items_ids: list[UUID],
        delivery_data: Delivery | None,
        checkout_items: list[AvailableCheckoutItem],
    ) -> str:
        invoices = make_order_invoices_objects(checkout_items, credit_items_ids)
        order_id = await self.order_repository.create(
            OrderORM(
                user_id=user.id,
                preorder_id=checkout_items[0].preorder_id,
                status=OrderStatus.UNPAID.value,
                delivery=(
                    DeliveryORM(
                        service=delivery_data.service,
                        address=delivery_data.point.address,
                        address_identifier=delivery_data.point.code,
                        recipient_name=delivery_data.recipient.full_name,
                        recipient_phone=delivery_data.recipient.phone,
                    )
                    if delivery_data
                    else None
                ),
                order_items=[
                    OrderItemORM(
                        item_id=item.id,
                        quantity=item.quantity,
                        price=item.price,
                        by_credit=item.id in credit_items_ids,
                        invoices=invoices.get(str(item.id), None),
                    )
                    for item in checkout_items
                ],
                invoices=invoices,
            )
        )

        receipt_items = [
            ReceiptItem(
                name=item.title,
                price=item.price_converted,
                quantity=item.quantity,
                amount=item.amount_converted,
            )
            for item in checkout_items
        ]

        init_payment_created_at = pendulum.now(tz='Europe/Moscow').replace(microsecond=0)
        init_payment_due_date = init_payment_created_at.add(hours=HOURS_TILL_ORDER_EXPIRES)

        payment = await self.tinkoff_client.init_payment(
            InitPaymentRequest(
                amount=sum([item.amount for item in receipt_items]),
                order_id=invoices['INITIAL'].id,
                description=f'Номер заказа: {order_id}',
                data={'Phone': user.traits.phone, 'Email': user.traits.email},
                redirect_due_date=init_payment_due_date,
                receipt=Receipt(
                    email=user.traits.email,
                    phone=user.traits.phone,
                    items=receipt_items,
                ),
            )
        )

        await self.order_repository.create(
            PaymentORM(
                created_at=init_payment_created_at,
                updated_at=init_payment_due_date,
                invoice_id=invoices['INITIAL'].id,
                url=payment.payment_url,
                status=payment.status,
                external_id=payment.payment_id,
            )
        )

        return payment.payment_url

    async def update_payment_status(self, payment_notification: PaymentStatusNotification) -> None:
        invoice = await self.order_repository.read(InvoiceORM, payment_notification.invoice_id)

        for payment in invoice.payments:
            if payment.external_id == payment_notification.payment_id:
                payment.status = payment_notification.status

                if new_invoice_status := PAYMENT_TO_INVOICE_STATUS_MAPPING.get(payment.status):
                    invoice.status = new_invoice_status.value

                if invoice.type == InvoiceType.INITIAL and (
                    new_order_status := INVOICE_TO_ORDER_STATUS_MAPPING.get(invoice.status)
                ):
                    invoice.order.status = new_order_status.value

    async def get_user_order(self, order_id: UUID, user_id: UUID) -> Order:
        order = await self.order_repository.read(
            db_model=OrderORM,
            ident=order_id,
        )

        if order.user_id != user_id:
            raise ForbiddenError

        order_items = []
        for item in order.order_items:
            credit = None
            if item.by_credit:
                item_unpaid_invoices = [
                    invoice for invoice in item.invoices if invoice.status == InvoiceStatus.UNPAID.value
                ]

                first_unpaid_invoice = next(iter(item_unpaid_invoices), None)

                credit = Credit(
                    payments=[CreditPart.model_validate(part) for part in item.info.credit_plan.parts],
                    paid_parts=(first_unpaid_invoice.credit_part_index if first_unpaid_invoice else len(item.invoices)),
                    invoice=(
                        Invoice(
                            id=first_unpaid_invoice.id,
                            credit_part_index=first_unpaid_invoice.credit_part_index,
                            type=first_unpaid_invoice.type,
                            amount=first_unpaid_invoice.amount,
                            is_paid=False,
                        )
                        if first_unpaid_invoice
                        else None
                    ),
                )

            order_items.append(
                OrderItem(
                    id=item.item_id,
                    title=item.info.product.title,
                    image=get_attachment_urls_by_type(item.info.product.attachments, AttachmentType.IMAGE)[0],
                    quantity=item.quantity,
                    sum=item.quantity * item.price,
                    credit=credit,
                )
            )

        formatted_preorder_date = order.preorder.created_at.strftime('%d.%m.%Y')
        return Order(
            id=order.id,
            created_at=order.created_at,
            status=order.status,
            items=order_items,
            preorder=PreorderInfo(
                id=order.preorder_id,
                title=f'Предзаказ от {formatted_preorder_date}',
                status=order.preorder.status,
                expected_arrival=order.preorder.expected_arrival,
            ),
            delivery=(
                Delivery(
                    service=order.delivery.service,
                    point=DeliveryPoint(address=order.delivery.address, code=order.delivery.address_identifier),
                    recipient=Recipient(
                        full_name=order.delivery.recipient_name,
                        phone=order.delivery.recipient_phone,
                    ),
                )
                if order.delivery
                else None
            ),
            invoices=[
                Invoice(
                    id=inv.id,
                    credit_part_index=None,
                    type=InvoiceType(inv.type),
                    amount=inv.amount,
                    is_paid=inv.status == InvoiceStatus.PAID.value,
                )
                for inv in order.invoices
                if inv.type != InvoiceType.CREDIT.value
            ],
            tracking=(
                Tracking(
                    code=order.delivery.track_code,
                    link=DELIVERY_TRACKING_LINK_MAPPING.get(order.delivery.service) + order.delivery.track_code,
                )
                if order.delivery and order.delivery.track_code
                else None
            ),
        )
