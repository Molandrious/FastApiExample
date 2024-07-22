from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Depends
from starlette import status
from starlette.requests import Request

from services import CatalogService
from services.user.constants import IncrementActionType
from services.user.models import CartItem, UserItems
from services.user.service import UserService
from transport.depends import get_catalog_service, get_user_service
from transport.middlewares.logging_middleware import FastAPILoggingRoute
from utils import USER_IDENTITY_CTX

user_router = APIRouter(tags=['user'], prefix='/user', route_class=FastAPILoggingRoute)


@user_router.get(
    path='/items',
    status_code=status.HTTP_200_OK,
    response_model=UserItems,
)
async def get_user_items(
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
) -> UserItems:
    if not (user := USER_IDENTITY_CTX.get()):
        return UserItems(
            cart=[
                CartItem(id=item_id, quantity=quantity) for item_id, quantity in request.session.get('cart', {}).items()
            ],
        )

    return await user_service.get_user_items(user_id=user.id)


@user_router.delete(
    path='/cart',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_items_from_cart(
    item_ids: list[UUID],
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
) -> None:
    if not (user := USER_IDENTITY_CTX.get()):
        cart = request.session.get('cart', {})
        for item_id in item_ids:
            cart.pop(item_id)
        return

    await user_service.remove_items_from_cart(user_id=user.id, item_ids=item_ids)


@user_router.post(
    path='/cart',
    status_code=status.HTTP_201_CREATED,
)
async def add_item_to_cart(
    user_service: Annotated[UserService, Depends(get_user_service)],
    item_id: UUID,
    request: Request,
) -> None:
    if not (user := USER_IDENTITY_CTX.get()):
        request.session.get('cart').update({str(item_id): 1})
        return

    await user_service.add_item_to_cart(user_id=user.id, item_id=item_id)


@user_router.patch(
    path='/cart',
    status_code=status.HTTP_200_OK,
)
async def change_cart_item_quantity(
    user_service: Annotated[UserService, Depends(get_user_service)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    item_id: UUID,
    action: IncrementActionType,
    request: Request,
) -> None:
    catalog_item_quantity = await catalog_service.get_catalog_item_quantity(item_id=item_id)

    await user_service.change_cart_item_quantity(
        item_id=item_id,
        session_cart=request.session.get('cart'),
        available_items=catalog_item_quantity.available,
        is_increment_action=action == IncrementActionType.INCREMENT,
    )


@user_router.post(
    path='/favorites',
    status_code=status.HTTP_201_CREATED,
)
async def add_favorite(
    user_service: Annotated[UserService, Depends(get_user_service)],
    item_id: UUID,
):
    await user_service.add_favorite_item(
        catalog_item_id=item_id,
        user_id=USER_IDENTITY_CTX.get().id,
    )


@user_router.delete(
    path='/favorites',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_favorite(
    user_service: Annotated[UserService, Depends(get_user_service)],
    item_id: UUID,
):
    await user_service.remove_favorite_item(
        catalog_item_id=item_id,
        user_id=USER_IDENTITY_CTX.get().id,
    )
