from abc import ABC
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel, to_pascal


class SGBaseModel(BaseModel, ABC):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class BaseEntity(SGBaseModel):
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BasePascalModel(SGBaseModel):
    model_config = ConfigDict(alias_generator=to_pascal)


class IdResponse(SGBaseModel):
    id: UUID
