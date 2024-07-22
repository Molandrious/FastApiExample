from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request

from services import CatalogService
from services.catalog.models import AvailableCheckoutItem
from services.order.errors import CheckoutDataIsEmptyError, InvalidCheckoutDataError
from services.order.models import Order
from services.order.service import OrderService
from services.user.service import UserService
from transport.constants import SESSION_CHECKOUT_DATA_KEY
from transport.depends import get_catalog_service, get_order_service, get_user_service
from transport.depends.auth import check_customer_access
from transport.handlers.client.order.schemas import (
    CreateOrderRequestSchema,
    CreateOrderResponseSchema,
    GetCheckoutDataResponseSchema,
    MakeCheckoutRequestSchema,
)
from transport.middlewares.logging_middleware import FastAPILoggingRoute
from utils import USER_IDENTITY_CTX

order_router = APIRouter(
    tags=['order'],
    route_class=FastAPILoggingRoute,
    dependencies=[Depends(check_customer_access)],
)


@order_router.post(
    path='/checkout',
    status_code=status.HTTP_201_CREATED,
)
async def make_checkout(
    request: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    request_data: MakeCheckoutRequestSchema,
):
    cart_items_availability = await catalog_service.verify_checkout_data(
        checkout_items=request_data.items,
    )

    if cart_items_availability.adjusted_items:
        await user_service.update_cart_items(
            user_id=USER_IDENTITY_CTX.get().id,
            updated_cart_items=cart_items_availability.adjusted_items,
        )
        raise InvalidCheckoutDataError

    request.session.update(
        {SESSION_CHECKOUT_DATA_KEY: [item.model_dump_json() for item in cart_items_availability.available_items]}
    )


@order_router.get(
    path='/checkout',
    status_code=status.HTTP_200_OK,
    response_model=GetCheckoutDataResponseSchema,
)
async def get_checkout_data(request: Request):
    if not (checkout_data := request.session.get(SESSION_CHECKOUT_DATA_KEY, [])):
        raise CheckoutDataIsEmptyError

    return GetCheckoutDataResponseSchema(
        items=[AvailableCheckoutItem.model_validate_json(item) for item in checkout_data]
    )


@order_router.post(
    path='/order',
    summary='Make order',
    status_code=200,
    response_model=CreateOrderResponseSchema,
)
async def make_order_entrypoint(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    order: CreateOrderRequestSchema,
    request: Request,
):
    if not (checkout_data := request.session.get(SESSION_CHECKOUT_DATA_KEY, [])):
        raise CheckoutDataIsEmptyError

    checkout_items = [AvailableCheckoutItem.model_validate_json(item) for item in checkout_data]

    is_preorder = any(item.preorder_id for item in checkout_items)

    if not is_preorder and not (order.delivery_data.recipient or order.delivery_data or order.delivery_data.service):
        raise InvalidCheckoutDataError

    await catalog_service.reserve_catalog_items(items=checkout_items)

    payment_link = await order_service.create_order(
        user=USER_IDENTITY_CTX.get(),
        credit_items_ids=order.credit_ids,
        delivery_data=order.delivery_data if not is_preorder else None,
        checkout_items=[AvailableCheckoutItem.model_validate_json(item) for item in checkout_data],
    )

    await user_service.remove_items_from_cart(
        user_id=USER_IDENTITY_CTX.get().id,
        item_ids=[item.id for item in checkout_items],
    )

    return CreateOrderResponseSchema(payment_link=payment_link)


#
# @order_router.get(
#     path='/payment-link',
#     status_code=status.HTTP_200_OK,
# )
# async def get_payment_link_entrypoint(
#     order_service: Annotated[OrderService, Depends(get_order_service)],
#     invoice_id: UUID,
# ):
#     pass
#


@order_router.get(
    path='/order-list',
    status_code=status.HTTP_200_OK,
)
async def get_order_list_entrypoint(order_service: Annotated[OrderService, Depends(get_order_service)]):  # noqa
    pass


@order_router.get(path='/order', status_code=status.HTTP_200_OK, response_model=Order)
async def get_order_entrypoint(
    order_service: Annotated[OrderService, Depends(get_order_service)],
    order_id: UUID,
) -> Order:
    return await order_service.get_user_order(
        order_id=order_id,
        user_id=USER_IDENTITY_CTX.get().id,
    )
