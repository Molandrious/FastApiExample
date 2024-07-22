from contextlib import suppress
from time import time
from typing import Any, ClassVar

from collections.abc import Callable

import sentry_sdk
from httpx import AsyncClient, AsyncHTTPTransport, ConnectError, HTTPStatusError, Request, Response, TimeoutException
from loguru import logger
from pydantic.alias_generators import to_snake
from sentry_sdk import Scope

from errors import ServerError
from errors.transport import LoggingError
from settings import Settings
from utils import dump_json, TRACE_ID


async def _trace_id_header_event_hook(
    request: Request,
) -> None:
    logger.trace('Event HTTPX: trace_id_header_event_hook')
    try:
        trace_id = TRACE_ID.get()
    except LookupError:
        return
    if request.headers.get(Settings().trace_id_header) is None:
        request.headers[Settings().trace_id_header] = trace_id


def _get_request_object(
    request: Request | None,
    response: Response | None,
) -> Request | None:
    if response:
        with suppress(RuntimeError):
            return response.request
    return request


def _make_input_data(
    request: Request | None,
) -> str | None:
    if not request:
        return None
    if request.url.params:
        return dump_json(dict(request.url.params))
    return request.content.decode() if request.content else None


def _make_method(
    request: Request | None,
) -> str:
    if request is None:
        return ''
    port_suffix = f':{request.url.port}' if request.url.port else ''
    return f'{request.url.scheme}://{request.url.host}{port_suffix}{request.url.path}'


async def _log_httpx_request(
    destination: str,
    request: Request | None,
    response: Response | None = None,
    error: Exception | None = None,
    started_at: float | None = None,
) -> None:
    request = _get_request_object(
        request=request,
        response=response,
    )
    request_headers = request.headers if request else None
    response_headers = response.headers if response else None
    response_data = None
    processing_time = None

    if response:
        if not hasattr(response, '_content'):
            await response.aread()

        with suppress(RuntimeError):
            response_data = response.text if response else None

        try:
            processing_time = response.elapsed.total_seconds()
        except RuntimeError:
            processing_time = time() - started_at if started_at else None

    if isinstance(response_data, str) and response_data.endswith('='):
        response_data = 'base64 content ...'
    input_data = None

    try:
        input_data = _make_input_data(request)
    except (ValueError, UnicodeDecodeError) as exc:
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        pass
    try:
        logger.info(
            {
                'destination': destination,
                'http_method': request.method if request else None,
                'method': _make_method(request),
                'processing_time': processing_time,
                'http_status_code': response.status_code if response else None,
                'input_data': input_data,
                'output_data': response_data,
                'request_headers': dict(request_headers) if request_headers else None,
                'response_headers': dict(response_headers) if response_headers else None,
                'error': error,
            },
        )
    except Exception as exc:
        try:
            raise LoggingError(debug=str(exc)) from exc  # noqa
        except LoggingError as exc:
            scope = Scope.get_current_scope()
            scope.set_extra(exc.__class__.__name__, str(exc))
            sentry_sdk.capture_exception(exc)


class LoggingAsyncHTTPTransport(
    AsyncHTTPTransport,
):
    def __init__(
        self,
        destination: str,
        **kwargs: Any,
    ) -> None:
        self._destination = destination
        super().__init__(**kwargs)

    async def handle_async_request(
        self,
        request: Request,
    ) -> Response:
        error: Exception | None = None
        response: Response | None = None
        started_at = time()
        try:
            response = await super().handle_async_request(request)
        except HTTPStatusError as exc:
            response = exc.response
            error = exc
            raise
        except ConnectError as exc:
            error = exc
            raise ServerError(debug=f'Не удалось подключиться к {self._destination}') from exc
        except TimeoutException as exc:
            error = exc
            timeout = request.extensions.get('timeout', {}).get('connect', None)
            timeout_str = f'({int(timeout)} секунд)' if timeout else ''
            raise ServerError(debug=f'Превышено ожидание по таймауту {timeout_str} к {self._destination}') from exc
        except Exception as exc:
            error = exc
            raise
        finally:
            await _log_httpx_request(
                destination=self._destination,
                request=request,
                response=response,
                error=error,
                started_at=started_at,
            )
        return response


class BaseApiClient(AsyncClient):
    _base_url: str
    _headers: ClassVar[dict[str, str]] = {'Content-Type': 'application/json'}
    _timeout: int = 5.0
    _default_event_hooks: ClassVar[dict[str, list[Callable[..., Any]]]] = {
        'request': [
            _trace_id_header_event_hook,
        ],
    }
    _logging: bool = True

    def __init__(self) -> None:
        self._destination = to_snake(self.__class__.__name__.replace('Client', ''))
        super().__init__(
            base_url=self._base_url,
            headers=self._headers,
            timeout=self._timeout,
            transport=(
                LoggingAsyncHTTPTransport(
                    destination=self._destination,
                )
                if self._logging
                else None
            ),
        )
        self.event_hooks.update(self._default_event_hooks)
