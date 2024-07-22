class BaseError(Exception):
    status_code: int
    message: str
    debug: str
    sentry_id: str = ''
    capture_by_sentry: bool = False

    @property
    def title(self) -> str:
        return self.__class__.__name__

    def as_dict(self, *, is_debug: bool = False) -> dict:
        debug = {'debug': self.debug} if is_debug else {}
        return dict(
            title=self.title,
            message=self.message,
            **debug,
        )


class ServerError(BaseError):
    status_code: int = 520
    message: str = 'Что-то пошло не так.'
    capture_by_sentry: bool = True
    sentry_id: str | None = None

    def __init__(
        self,
        message: str | None = None,
        debug: str | None = None,
    ):
        self.message = message or self.message
        self.debug = debug
        super().__init__()


class ExpectedError(ServerError):
    capture_by_sentry = False
