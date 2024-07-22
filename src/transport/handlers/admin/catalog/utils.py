from fastapi import Form, UploadFile
from fastapi.exceptions import RequestValidationError
from loguru import logger
from orjson import loads

from services.catalog.models import FilterGroup, PhysicalProperties
from transport.handlers.admin.catalog.schemas import (
    CreateProductSchema,
)


async def parce_create_product_form(
    images: list[UploadFile],
    title: str = Form(...),
    description: str | None = Form(default=None),
    categoryLink: str = Form(alias='categoryLink'),  # noqa
    physicalProperties: str = Form(alias='physicalProperties'),  # noqa
    filterGroups: str = Form(alias='filterGroups'),  # noqa
) -> CreateProductSchema:
    try:
        return CreateProductSchema(
            title=title,
            description=description,
            category_link=categoryLink,
            physical_properties=PhysicalProperties.model_validate_json(physicalProperties),
            images=[image.file.read() for image in images],
            filter_groups=[FilterGroup.model_validate(group) for group in loads(filterGroups)],
        )
    except Exception as e:
        logger.error(e)
        raise RequestValidationError from e
