from typing import Any

import sqlalchemy
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept


def force_default_column_arguments_before_commit(mapper: Mapper | None = None) -> None:
    if not mapper:
        mapper = sqlalchemy.orm.Mapper

    def instant_defaults_listener(
        target: DeclarativeAttributeIntercept,
        _: Any,
        kwargs: dict[str, Any],
    ) -> None:
        original = kwargs.copy()
        kwargs.clear()

        for key, column in sqlalchemy.inspect(target.__class__).columns.items():
            if column.description == 'id' and hasattr(column, 'default') and column.default is not None:
                if callable(column.default.arg):
                    kwargs[key] = column.default.arg(target)
                else:
                    kwargs[key] = column.default.arg

        kwargs.update(original)

    sqlalchemy.event.listen(mapper, 'init', instant_defaults_listener)
