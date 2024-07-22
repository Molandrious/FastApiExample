from io import BytesIO
from uuid import uuid4

from PIL import Image

from services.file_manager.constants import IMAGE_SIZED_BREAKPOINTS


def compress_and_resize(
    file: bytes,
    file_identifier: str | None = None,
) -> dict[str, BytesIO]:
    original_image = Image.open(BytesIO(file))
    if not file_identifier:
        file_identifier = uuid4()

    in_memory_files = {}
    for postfix, size_limit in IMAGE_SIZED_BREAKPOINTS.items():
        img = original_image.copy()

        if img.width > img.height:
            max_size = img.width
            aspect_ratio = img.height / img.width
            new_size = (size_limit, int(aspect_ratio * size_limit))
        else:
            max_size = img.height
            aspect_ratio = img.width / img.height
            new_size = (int(aspect_ratio * size_limit), size_limit)

        if max_size > size_limit:
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        img_byte_arr = BytesIO()
        img.convert('RGB').save(img_byte_arr, format='WEBP', optimize=True, quality=80)

        img_byte_arr.seek(0)
        in_memory_files[f'{file_identifier}_{postfix}.webp'] = img_byte_arr

    return in_memory_files
