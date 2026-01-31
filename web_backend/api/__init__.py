"""
Tezbarakat Telegram Bot - API 路由包
"""

from fastapi import APIRouter
from .dashboard import router as dashboard_router
from .accounts import router as accounts_router
from .groups import router as groups_router
from .keywords import router as keywords_router
from .messages import router as messages_router
from .config import router as config_router
from .auth import router as auth_router
from .websocket import router as websocket_router

# 创建主路由
api_router = APIRouter(prefix="/api")

# 注册所有子路由
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(accounts_router)
api_router.include_router(groups_router)
api_router.include_router(keywords_router)
api_router.include_router(messages_router)
api_router.include_router(config_router)
api_router.include_router(websocket_router)

__all__ = ['api_router']
