from database.constants import AttachmentType
from database.models import AttachmentORM, ProductORM
from services.catalog.models import FilterDTO, FilterGroup


def prepare_filter_groups(item: ProductORM) -> list[FilterGroup]:
    filter_groups = {}

    for filter in item.filters:
        if filter.group.title not in filter_groups:
            filter_groups[filter.group.title] = FilterGroup(
                id=filter.group.id,
                title=filter.group.title,
                filters=[],
            )

        filter_groups[filter.group.title].filters.append(FilterDTO(id=filter.id, value=filter.value))

    return list(filter_groups.values())


def get_attachment_urls_by_type(attachments: list[AttachmentORM], attachment_type: AttachmentType) -> list[str]:
    return [att.url for att in attachments if att.type == attachment_type.value]
