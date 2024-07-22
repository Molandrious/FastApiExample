from collections.abc import Callable
from typing import Any

from starlette.requests import Request


async def query_params_key_builder(
    _func: Callable[..., Any],
    namespace: str = '',
    *,
    request: Request = None,
    **_kwargs: Any,
):
    return ':'.join([namespace, request.method.lower(), request.url.path])
