from traceback import format_exc, print_exc


from fastapi import Request
from sentry_sdk import capture_exception, Scope
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from errors import ServerError
from settings import Settings
from transport.error_handlers import process_server_error


class ErrorsHandlerMiddleware(BaseHTTPMiddleware):
    is_debug: Settings()

    def __init__(
        self,
        *,
        app: ASGIApp,
        is_debug: bool,
    ) -> None:
        super().__init__(app)
        self.is_debug = is_debug

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        settings = Settings()
        try:
            return await call_next(request)
        except ServerError as exc:
            return process_server_error(
                request=request,
                exc=exc,
                sentry_id=None,
                is_debug=self.is_debug,
            )
        except Exception as exc:
            print_exc()
            scope = Scope.get_current_scope()
            if trace_id := request.scope.get(settings.trace_id_header):
                scope.set_tag(settings.trace_id_header, trace_id)
            sentry_id = capture_exception(exc)
            return process_server_error(
                request=request,
                exc=ServerError(debug=format_exc()),
                sentry_id=sentry_id,
                is_debug=self.is_debug,
            )
