from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select

from database.models import BaseORM
from database.repositories.base import ISqlAlchemyRepository


class CRUDRepository[Model: type[BaseORM]](ISqlAlchemyRepository):
    db_model: Model

    def __init__(self, db_model: Model) -> None:
        self.db_model = db_model
        super().__init__()

    async def create(self, entity: BaseModel) -> UUID:
        db_object = self.db_model(**entity.model_dump())
        self.session.add(db_object)
        return db_object.id

    async def create_many(self, entities: list[BaseModel]) -> Sequence[UUID]:
        db_objects = [self.db_model(**entity.model_dump()) for entity in entities]
        self.session.add_all(db_objects)
        return [db_object.id for db_object in db_objects]

    async def read_by(self, count: int | None = None, **kwargs) -> Sequence[Model]:
        stmt = select(self.db_model).where(**kwargs).limit(count)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalars().all()

    async def read_one_by(self, **kwargs) -> Model | None:
        stmt = select(self.db_model).filter_by(**kwargs).limit(1)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalar_one_or_none()

    async def read(self, id: UUID) -> Model:
        db_object = await self.session.get(self.db_model, id)
        return db_object

    async def read_all(self) -> Sequence[Model]:
        stmt = select(self.db_model)
        db_objects = await self.session.execute(stmt)
        return db_objects.scalars().all()

    async def update[Model: BaseModel](self, id: UUID, entity: Model) -> Model:
        if (db_object := await self.session.get(self.db_model, id)) is None:
            raise ValueError('Entity not found')
        for key, value in entity.model_dump(exclude_unset=True).items():
            setattr(db_object, key, value)

        return db_object

    async def delete(self, id: UUID) -> None:
        db_object = await self.session.get(self.db_model, id)
        if db_object:
            await self.session.delete(db_object)
