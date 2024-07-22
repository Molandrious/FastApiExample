import contextlib

from jinja2 import Template
from loguru import logger
from singleton_decorator import singleton
from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, AsyncSession, create_async_engine

from database.models import BaseDeclarative
from settings import Settings

from utils import TRACE_ID


@singleton
class SQLAlchemyClient:
    _db_connection_string_template: Template = Template(
        source='{{ driver }}://{{ user }}:{{ password }}@{{ host }}:{{ port }}/{{ database }}',
        autoescape=True,
    )

    def __init__(self):
        logger.debug(f'SQLAlchemy client init with {Settings().env.postgres.model_dump()}')
        self.engine = create_async_engine(
            url=self._db_connection_string_template.render(**Settings().env.postgres.model_dump()),
            echo=Settings().env.debug_sql_alchemy,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=500,
            pool_timeout=10,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self._ctx_session_manager = async_scoped_session(
            async_sessionmaker(autoflush=True, expire_on_commit=False, bind=self.engine),
            scopefunc=TRACE_ID.get,
        )

    def get_session(self) -> AsyncSession:
        return self._ctx_session_manager()

    async def close_ctx_session(self) -> None:
        await self._ctx_session_manager.remove()

    def connect(self):
        self.engine.connect()
        logger.trace('Database connected')

    async def close(self):
        await self.engine.dispose()
        logger.trace('Database disconnected')

    async def clear_all_tables(self) -> None:
        metadata = BaseDeclarative.metadata
        async with self.get_session() as session:
            for table in reversed(metadata.sorted_tables):
                with contextlib.suppress(DatabaseError):
                    await session.execute(table.delete())
            await session.commit()

    async def create_all_tables(self) -> None:
        metadata = BaseDeclarative.metadata
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
