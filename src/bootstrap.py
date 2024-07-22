from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

import sentry_sdk
from fastapi import APIRouter, Depends, FastAPI
from fastapi.routing import APIRoute
from loguru import logger
from pydantic.alias_generators import to_camel
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from integrations.redis.client import RedisClient
from integrations.sql_alchemy.client import SQLAlchemyClient
from logger import AppLogger
from settings import Settings
from transport.depends import get_current_user, init_ctx_db_session
from transport.error_handlers import setup_fastapi_error_handlers
from transport.handlers import admin_router, market_router, notification_router, order_router, user_router
from transport.handlers.client.cdek_widget.entrypoints import cdek_router
from transport.middlewares import FastAPILoggingRoute, TraceIdMiddleware
from transport.middlewares.errors_handler_middleware import ErrorsHandlerMiddleware
from transport.middlewares.prepare_session_middleware import PrepareSessionMiddleware
from utils import get_release_version


@asynccontextmanager
async def _lifespan(
    app: FastAPI,  # noqa
) -> AsyncGenerator[None, None]:
    logger.trace('Lifespan started')

    SQLAlchemyClient().connect()
    await SQLAlchemyClient().create_all_tables()

    redis = RedisClient()
    await redis.check_connection()
    redis.init_cache()

    yield

    await SQLAlchemyClient().close()
    await RedisClient().close()
    logger.trace('Lifespan finished')


def setup_api_routers(
    app: FastAPI,
) -> None:
    api_router = APIRouter(
        prefix='/api',
        dependencies=[
            Depends(init_ctx_db_session),
            Depends(get_current_user),
        ],
        route_class=FastAPILoggingRoute,
    )

    callback_router = APIRouter(
        prefix='/callback',
        route_class=FastAPILoggingRoute,
    )

    callback_router.include_router(notification_router)

    api_router.include_router(admin_router)
    api_router.include_router(market_router)
    api_router.include_router(user_router)
    api_router.include_router(order_router)
    api_router.include_router(cdek_router)
    api_router.include_router(callback_router)

    app.include_router(api_router)


def setup_entrypoints_query_params_camel_case_alias(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            for param in route.dependant.query_params:
                if param.name == param.field_info.alias:
                    param.field_info.alias = to_camel(param.name)


def setup_middlewares(
    app: FastAPI,
) -> None:
    settings = Settings()
    sentry_sdk.init(
        dsn=settings.env.sentry_dsn,
        enable_tracing=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        profiler_mode='thread',
        attach_stacktrace=True,
        max_request_body_size='always',
        release=get_release_version(),
        environment=settings.env.environment,
        send_default_pii=True,
        integrations=[
            LoguruIntegration(
                level=LoggingLevels.ERROR.value,
                event_level=LoggingLevels.CRITICAL.value,
            )
        ],
    )

    setup_fastapi_error_handlers(app, is_debug=settings.env.debug)
    app.add_middleware(ErrorsHandlerMiddleware, is_debug=settings.env.debug)
    app.add_middleware(PrepareSessionMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=settings.env.backend.session_secret_key)
    app.add_middleware(TraceIdMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*'],
    )


@lru_cache
def make_app() -> FastAPI:
    app = FastAPI(
        lifespan=_lifespan,
        debug=Settings().env.debug,
        logger=AppLogger.make(),
        docs_url='/',
    )

    setup_api_routers(app)
    setup_middlewares(app)
    setup_entrypoints_query_params_camel_case_alias(app)

    return app
