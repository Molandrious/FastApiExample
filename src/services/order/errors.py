from errors.base import ExpectedError, ServerError


class InvalidCheckoutDataError(ServerError):
    status_code = 400
    message = 'Неверные данные для оформления заказа'


class CheckoutDataIsEmptyError(ExpectedError):
    status_code = 400
    message = 'Отсутствуют данные для оформления заказа'
