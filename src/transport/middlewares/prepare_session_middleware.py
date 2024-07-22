from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class PrepareSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger.trace('PrepareSessionMiddleware')
        if not request.session:
            request.session.update(
                {
                    'cart': {},
                    'favorites': {},
                }
            )
        response = await call_next(request)
        return response
