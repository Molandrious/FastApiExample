from database.repositories import CatalogRepository, UserRepository
from database.repositories.order import OrderRepository


async def get_catalog_repository() -> CatalogRepository:
    yield CatalogRepository()


async def get_user_repository() -> UserRepository:
    yield UserRepository()


async def get_order_repository() -> OrderRepository:
    yield OrderRepository()
