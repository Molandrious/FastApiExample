from transport.handlers.admin.catalog.entrypoints import admin_router
from transport.handlers.client.catalog.entrypoints import market_router
from transport.handlers.client.order.entrypoints import order_router
from transport.handlers.client.user.entrypoints import user_router
from transport.handlers.internal.notifications.entrypoints import notification_router

__all__ = [
    'user_router',
    'notification_router',
    'order_router',
    'market_router',
    'admin_router',
]
