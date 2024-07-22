from contextvars import ContextVar
from typing import Any

import orjson
from poetry.toml import TOMLFile

from integrations.ory_kratos.models import UserIdentity
from settings import Settings

TRACE_ID: ContextVar[str] = ContextVar('TraceId', default='trace_id')
USER_IDENTITY_CTX: ContextVar[UserIdentity | None] = ContextVar('UserIdentity')


def get_release_version() -> str:
    return TOMLFile(path=Settings().root_path.joinpath('pyproject.toml')).read()['tool']['poetry']['version']


def dump_json(
    data: str | dict[str, Any] | list[dict[str, Any]],
    default: Any = None,
) -> str:
    if isinstance(data, str):
        return data

    option = orjson.OPT_NON_STR_KEYS | orjson.OPT_SORT_KEYS
    return orjson.dumps(
        data,
        default=default,
        option=option,
    ).decode()
