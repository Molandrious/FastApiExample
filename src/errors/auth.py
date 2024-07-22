from errors.base import ExpectedError


class UnauthorizedError(ExpectedError):
    status_code = 401
    message = 'Отсутствует доступ для неавторизованного пользователя.'


class UnverifiedError(ExpectedError):
    status_code = 401
    message = 'Пользователь не подтвердил свою почту'


class ForbiddenError(ExpectedError):
    status_code = 403
    message = 'Недостаточно прав'
