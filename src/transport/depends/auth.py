from typing import Annotated

from fastapi import Depends
from loguru import logger
from sentry_sdk.scope import Scope
from starlette.requests import Request

from errors.auth import ForbiddenError, UnauthorizedError, UnverifiedError
from integrations.ory_kratos.client import OryKratosClient
from integrations.ory_kratos.models import UserIdentity
from settings import Settings
from utils import USER_IDENTITY_CTX


async def get_current_user(request: Request) -> UserIdentity | None:
    logger.trace('Get current user')

    if not request.cookies.get(Settings().env.ory_kratos.session_cookie):
        USER_IDENTITY_CTX.set(None)
        return None

    async with OryKratosClient() as client:
        session = await client.get_session(request.cookies)

    if not session:
        USER_IDENTITY_CTX.set(None)
        return None

    user_identity = UserIdentity(
        id=session['identity']['id'],
        schema_id=session['identity']['schema_id'],
        state=session['identity']['state'],
        traits=session['identity']['traits'],
        verified=any(addr['verified'] for addr in session['identity']['verifiable_addresses']),
        metadata_public=session['identity']['metadata_public'],
    )

    request.session.update({'cart': {}})

    USER_IDENTITY_CTX.set(user_identity)
    scope: Scope = Scope.get_current_scope()

    scope.set_user({'email': user_identity.traits.email, 'user_id': str(user_identity.id)})

    return user_identity


async def check_customer_access(
    user_identity: Annotated[UserIdentity | None, Depends(get_current_user)],
) -> UserIdentity:
    if not user_identity:
        raise UnauthorizedError

    if not user_identity.verified:
        raise UnverifiedError

    return user_identity


async def check_admin_access(user_identity: Annotated[UserIdentity, Depends(check_customer_access)]) -> UserIdentity:
    if not user_identity.schema_id == Settings().env.ory_kratos.admin_schema:
        raise ForbiddenError

    return user_identity
