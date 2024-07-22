from uuid import UUID

from database.models import InvoiceORM
from services.catalog.models import AvailableCheckoutItem
from services.order.constants import (
    InvoiceStatus,
    InvoiceType,
)


def make_order_invoices_objects(
    checkout_items: list[AvailableCheckoutItem], credit_items_ids: list[UUID]
) -> dict[str, InvoiceORM | list[InvoiceORM]]:
    if not credit_items_ids:
        return {
            'INITIAL': InvoiceORM(
                title='Оплата заказа',
                type=InvoiceType.INITIAL.value,
                amount=sum([item.price * item.quantity for item in checkout_items]),
                status=InvoiceStatus.UNPAID.value,
            )
        }

    initial_sum = 0
    credit_item_invoices = {}

    for item in checkout_items:
        if item.credit_parts:
            item_invoices = []
            for index, part in enumerate(item.credit_parts):
                if index == 0:
                    initial_sum += part.sum * item.quantity
                    continue

                item_invoices.append(
                    InvoiceORM(
                        title='Оплата рассрочки',
                        credit_part_index=index,
                        type=InvoiceType.CREDIT.value,
                        amount=part.sum * item.quantity,
                        status=InvoiceStatus.UNPAID.value,
                    )
                )

            credit_item_invoices[str(item.id)] = sorted(item_invoices, key=lambda x: x.credit_part_index)
        else:
            initial_sum += item.price * item.quantity

    initial_invoice = InvoiceORM(
        title='Оплата депозита заказа',
        type=InvoiceType.INITIAL.value,
        amount=initial_sum,
        status=InvoiceStatus.UNPAID.value,
    )

    return {
        'INITIAL': initial_invoice,
        **credit_item_invoices,
    }
