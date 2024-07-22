from abc import ABC
from collections.abc import Sequence
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import BaseORM
from integrations.sql_alchemy.client import SQLAlchemyClient

ORMModel = TypeVar('ORMModel', bound=BaseORM)


class ISqlAlchemyRepository(ABC):
    @property
    def session(self) -> AsyncSession:
        return SQLAlchemyClient().get_session()

    async def create(self, db_object: ORMModel) -> UUID:
        self.session.add(db_object)
        await self.session.flush()
        return db_object.id

    async def create_many(self, db_objects: list[ORMModel]) -> Sequence[UUID]:
        self.session.add_all(db_objects)
        return [db_object.id for db_object in db_objects]

    async def read_by(self, db_model: type[ORMModel], count: int | None = None, **kwargs) -> Sequence[ORMModel]:
        stmt = select(db_model).where(**kwargs).limit(count)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalars().all()

    async def read_one_by(self, db_model: type[ORMModel], **kwargs) -> ORMModel | None:
        stmt = select(db_model).filter_by(**kwargs).limit(1)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalar_one_or_none()

    async def read(self, db_model: type[ORMModel], ident: UUID) -> ORMModel:
        db_object = await self.session.get(db_model, ident)
        return db_object

    async def read_all(self, db_model: type[ORMModel]) -> Sequence[ORMModel]:
        stmt = select(db_model)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalars().all()

    async def update(self, object_model: type[BaseORM], identifier: UUID, **kwargs: Any):
        await self.session.execute(update(object_model).where(object_model.id == identifier).values(kwargs))

    async def update_with_read(self, updated_obj: ORMModel) -> ORMModel:
        db_object = await self.session.get(updated_obj.__class__, updated_obj.id)
        for key, value in updated_obj.__dict__.items():
            if key.startswith('_'):
                continue
            if hasattr(db_object, key):
                setattr(db_object, key, value)

        return db_object

    async def delete(self, object_model: type[BaseORM], id: UUID) -> None:
        db_object = await self.session.get(object_model, id)
        if db_object:
            await self.session.delete(db_object)
