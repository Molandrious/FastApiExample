from uuid import UUID

from pydantic import EmailStr

from base_objects.models import SGBaseModel


class UserNameEntity(SGBaseModel):
    first: str
    last: str


class Traits(SGBaseModel):
    email: EmailStr
    name: UserNameEntity
    phone: str

    @property
    def full_name(self) -> str:
        return f'{self.name.last} {self.name.first}'


class UserIdentity(SGBaseModel):
    id: UUID
    schema_id: str
    state: str
    traits: Traits
    verified: bool
    metadata_public: dict | None
