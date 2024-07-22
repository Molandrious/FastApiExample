from errors import ServerError
from errors.base import ExpectedError


class UnknownAnswerError(ServerError):
    status_code = 502
    message = 'Bad Gateway'
    capture_by_sentry = False


class ValidationError(ServerError):
    status_code = 400
    message = 'Ошибка проверки данных'
    capture_by_sentry = False


class InputValidationError(ServerError):
    status_code = 400
    message = 'Некорректный запрос'
    capture_by_sentry = False


class ResponseValidationError(ServerError):
    message = 'Ошибка валидации ответа'
    status_code = 500
    capture_by_sentry = False


class NotFoundError(ServerError):
    status_code = 404
    message = 'Pecypc не найден'
    capture_by_sentry = False


class LoggingError(ExpectedError):
    status_code = 500
    message = 'Внутренняя ошибка при работе c логами'
