from uuid import uuid4

from loguru import logger
from sentry_sdk import Scope
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from settings import Settings
from utils import TRACE_ID


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger.trace('TraceIdMiddleware')
        current_trace = request.headers.get(Settings().trace_id_header, str(uuid4()))
        TRACE_ID.set(current_trace)
        scope: Scope = Scope.get_current_scope()
        scope.set_extra('X-Trace-Id', TRACE_ID.get())
        response = await call_next(request)
        response.headers[Settings().trace_id_header] = current_trace
        return response
