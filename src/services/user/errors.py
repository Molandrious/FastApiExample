from errors.base import ExpectedError


class CartItemQuantityInvalidError(ExpectedError):
    status_code: int = 400
    message: str = 'Неверное кол-во единиц товара в корзине'
