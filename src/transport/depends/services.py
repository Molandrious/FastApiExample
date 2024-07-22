from typing import Annotated

from fastapi import Depends

from database.repositories import CatalogRepository, UserRepository
from database.repositories.order import OrderRepository
from integrations.s3.client import S3Client
from integrations.tinkoff.client import TinkoffClient
from services import CatalogService
from services.file_manager.service import FileManagerService
from services.order.service import OrderService
from services.user.service import UserService
from transport.depends.clients import get_s3_client, get_tinkoff_client
from transport.depends.repositories import get_catalog_repository, get_order_repository, get_user_repository


async def get_file_manager_service(
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
) -> FileManagerService:
    yield FileManagerService(s3_client=s3_client)


async def get_catalog_service(
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> CatalogService:
    yield CatalogService(catalog_repository=catalog_repository)


async def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    yield UserService(user_repository=user_repository)


async def get_order_service(
    order_repository: Annotated[OrderRepository, Depends(get_order_repository)],
    tinkoff_client: Annotated[TinkoffClient, Depends(get_tinkoff_client)],
) -> OrderService:
    yield OrderService(order_repository=order_repository, tinkoff_client=tinkoff_client)
