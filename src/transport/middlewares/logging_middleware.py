from abc import ABC
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from contextlib import suppress
from functools import partial
from json import JSONDecodeError
from time import time
from typing import Any, TypeVar

import sentry_sdk
from fastapi import Request, Response
from fastapi.routing import APIRoute
from loguru import logger
from sentry_sdk import Scope
from starlette.datastructures import UploadFile

from errors import ServerError
from errors.transport import LoggingError
from utils import dump_json

LOGGING_REQUEST_METHODS_WITHOUT_BODY = {'GET', 'DELETE'}
LOGGING_SUBSTRINGS_OF_ROUTES_FOR_SKIP = (
    'metrics',
    'swagger',
    'debug/health',
)
CONTENT_TYPE_REQUEST_PARSING_MAPPING = {
    'application/json': 'json',
    'multipart/form-data': 'form',
}


class FastAPIRequestWrapper:
    _request_object: Request

    def __init__(
        self,
        request_object: Request,
    ) -> None:
        self._request_object = request_object

    @property
    def headers(
        self,
    ) -> str | None:
        return dump_json(dict(self._request_object.headers))

    async def get_input_data(
        self,
    ) -> str | None:
        input_data = None
        if self._request_object.method.upper() not in LOGGING_REQUEST_METHODS_WITHOUT_BODY:
            with suppress(
                UnicodeDecodeError,
                RuntimeError,
                JSONDecodeError,
            ):
                input_data = await self._request_object.json()
        if params := self._request_object.query_params:
            input_data = input_data or {}
            input_data.update(params._dict)  # noqa

        if form := await self._request_object.form():
            input_data = input_data or {}
            form_file_names = []
            for item in form._list:
                if isinstance(item[1], UploadFile):
                    form_file_names.append(str(item[1].filename))
                    continue
                input_data.update({item[0]: item[1]})
            input_data.update({'files': form_file_names})

        return dump_json(input_data) if input_data else None

    @property
    def http_method(
        self,
    ) -> str | None:
        return self._request_object.method.upper()

    @property
    def method(
        self,
    ) -> str | None:
        return str(self._request_object.url.path)

    @property
    def path(self) -> str:
        return self._request_object.url.path


class FastAPIResponseWrapper:
    _response_object: Response

    def __init__(
        self,
        response_object: Response,
    ) -> None:
        self._response_object = response_object

    @property
    def headers(
        self,
    ) -> str:
        return dump_json(dict(self._response_object.headers))

    @property
    def output_data(
        self,
    ) -> str | None:
        output_data = None
        if not self._response_object.body:
            return output_data
        with suppress(
            UnicodeDecodeError,
        ):
            output_data = self._response_object.body.decode()
        return dump_json(output_data) if output_data else None

    @property
    def status_code(
        self,
    ) -> int:
        return self._response_object.status_code


LKRequest = TypeVar('LKRequest', bound=FastAPIRequestWrapper)
LKResponse = TypeVar('LKResponse', bound=FastAPIResponseWrapper)


class LoggingMiddlewareBase(
    ABC,
):
    request_cls: type[LKRequest]  # type: ignore
    response_cls: type[LKResponse]  # type: ignore
    logging_substrings_of_routes_for_skip: Sequence[str] = ()

    async def __call__(
        self,
        request: object,
        call_next: Callable[[object], Awaitable[object]],
    ) -> object:
        wrapped_request: LKRequest = self.request_cls(request)  # type: ignore
        wrapped_response: LKResponse | None = None
        http_status_code = None
        start_time = time()
        error = None
        try:
            response = await call_next(request)
            wrapped_response = self.response_cls(response)  # type: ignore
            http_status_code = wrapped_response.status_code
            return response  # noqa: TRY300
        except ServerError as exc:
            error = exc
            if not http_status_code:
                http_status_code = exc.status_code
            raise
        except Exception as exc:
            error = exc
            raise
        finally:
            try:
                if not any(
                    substring
                    for substring in self.logging_substrings_of_routes_for_skip
                    if substring in wrapped_request.path
                ):
                    logger.info(
                        {
                            'destination': 'internal',
                            'http_method': wrapped_request.http_method,
                            'method': wrapped_request.method,
                            'processing_time': time() - start_time,
                            'http_status_code': http_status_code,
                            'input_data': await wrapped_request.get_input_data(),
                            'output_data': wrapped_response.output_data if wrapped_response else None,
                            'request_headers': wrapped_request.headers,
                            'response_headers': wrapped_response.headers if wrapped_response else None,
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


class FastAPILoggingMiddleware(
    LoggingMiddlewareBase,
):
    request_cls = FastAPIRequestWrapper
    response_cls = FastAPIResponseWrapper


class FastAPILoggingRoute(
    APIRoute,
):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        middleware = FastAPILoggingMiddleware()
        original_route_handler = super().get_route_handler()
        return partial(
            middleware,
            call_next=original_route_handler,
        )
