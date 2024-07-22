from uuid import UUID

from database.constants import AttachmentType
from base_objects.models import SGBaseModel


class Attachment(SGBaseModel):
    product_id: UUID
    type: AttachmentType
    index: int
    url: str
