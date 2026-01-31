"""
Tezbarakat Telegram Bot - Web 后台 API 主入口
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import uvicorn

from config import settings
from models.database import init_db
from api import api_router


# 配置日志
logger.add(
    f"{settings.log_path}/web_backend.log",
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在启动 Web 后台 API...")
    
    # 初始化数据库
    try:
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    
    yield
    
    # 关闭时
    logger.info("Web 后台 API 正在关闭...")


# 创建 FastAPI 应用
# 生产环境禁用 API 文档以提高安全性
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Tezbarakat Telegram 智能营销机器人 - Web 管理后台 API",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None
)

# 配置 CORS
# 生产环境应该限制具体域名
if settings.debug:
    # 调试模式下，如果未配置，则允许所有
    allowed_origins = settings.cors_origins if settings.cors_origins else ["*"]
else:
    # 生产模式下，只允许配置的非通配符域名
    allowed_origins = [
        origin for origin in settings.cors_origins if origin != "*"
    ]
    if not allowed_origins:
        logger.warning("生产环境中未配置具体的 CORS 源 (CORS_ORIGINS)，将禁用所有来自浏览器的跨域请求。")

# 只有在 allowed_origins 列表非空时才添加 CORS 中间件
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            # 生产环境不暴露详细错误信息
            "detail": str(exc) if settings.debug else None
        }
    )


# 注册 API 路由
app.include_router(api_router)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.app_version}


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs" if settings.debug else "disabled"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
