from loguru import logger
from starlette.requests import Request

from errors.base import ExpectedError
from integrations.sql_alchemy.client import SQLAlchemyClient


async def init_ctx_db_session(request: Request) -> None:
    logger.trace('DB session dependency')

    try:
        yield
        if request.method != 'GET':
            await SQLAlchemyClient().get_session().commit()
    except Exception as error:
        if not issubclass(type(error), ExpectedError) and request.method != 'GET':
            logger.debug('Rollback transaction')
            await SQLAlchemyClient().get_session().rollback()
        raise
    finally:
        await SQLAlchemyClient().close_ctx_session()
