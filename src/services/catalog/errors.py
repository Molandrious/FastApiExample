from errors.base import BaseError


class CategoryNotFoundError(BaseError):
    status_code: int = 404
    message: str = 'Категория не найдена'


class IncorrectItemsSectionsError(BaseError):
    status_code: int = 400
    message: str = 'Товары состоят в разных секциях'
