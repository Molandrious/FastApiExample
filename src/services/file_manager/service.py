import asyncio
from uuid import UUID, uuid4

from database.constants import AttachmentType
from integrations.s3.client import S3Client
from integrations.s3.errors import S3UploadFileError
from services.file_manager.models import Attachment
from services.file_manager.utils import compress_and_resize
from settings import Settings


class FileManagerService:
    def __init__(
        self,
        s3_client: S3Client,
    ) -> None:
        self._s3_client = s3_client

    async def upload_product_images(
        self,
        product_id: UUID,
        images: list[bytes],
    ) -> list[Attachment]:
        attachments = []

        key_prefix = f'products/{product_id}'
        for index, image in enumerate(images):
            image_identifier = str(uuid4())
            image_variations = await asyncio.to_thread(compress_and_resize, image, image_identifier)

            for title, file in image_variations.items():
                try:
                    await self._s3_client.upload_file(
                        file=file,
                        key=f'{key_prefix}/{title}',
                    )
                except Exception as exc:
                    raise S3UploadFileError(debug=str(exc)) from exc

            attachments.append(
                Attachment(
                    product_id=product_id,
                    url=f'{Settings().env.s3.public_url}/{key_prefix}/{image_identifier}',
                    type=AttachmentType.IMAGE,
                    index=index,
                )
            )

        return attachments
