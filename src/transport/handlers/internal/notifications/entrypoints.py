from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from errors.transport import UnknownAnswerError
from integrations.tinkoff.models import PaymentStatusNotification
from services.order.service import OrderService
from transport.depends import get_current_user, get_order_service
from transport.middlewares.logging_middleware import FastAPILoggingRoute
from utils import USER_IDENTITY_CTX

notification_router = APIRouter(route_class=FastAPILoggingRoute, prefix='/notifications', tags=['notifications'])


@notification_router.post(
    status_code=status.HTTP_200_OK,
    path='/payment-status',
)
async def notification_handler(
    notification_data: PaymentStatusNotification,
    order_service: Annotated[OrderService, Depends(get_order_service)],
):
    if not notification_data.verify():
        raise UnknownAnswerError

    await order_service.update_payment_status(payment_notification=notification_data)

    return 'OK'


@notification_router.get(
    status_code=status.HTTP_200_OK,
    path='/ory_test',
    dependencies=[Depends(get_current_user)],
)
async def get_current_user_her():
    return USER_IDENTITY_CTX.get()


@notification_router.get(
    status_code=status.HTTP_200_OK,
    path='/ory_test_err',
    dependencies=[Depends(get_current_user)],
)
async def get_current_user_err():
    raise KeyError
    # return USER_IDENTITY_CTX.get()
