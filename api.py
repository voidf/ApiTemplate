import os
from fastapi import FastAPI, HTTPException, Request
from loguru import logger
logger.add('log/site_{time}.log', rotation="1 day", compression="zip")
import tracemalloc
import uvicorn
tracemalloc.start()

from config import static
from typing import *
from fastapi.middleware.cors import CORSMiddleware
# from models.submission import Submission
from model import *
from content_size_limit_asgi import ContentSizeLimitMiddleware, ContentSizeExceeded
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic.json import ENCODERS_BY_TYPE
from bson.objectid import ObjectId
ENCODERS_BY_TYPE[ObjectId] = lambda x: str(x) # ObjectID直接转str


def preload() -> FastAPI:
    """多worker fork出来前先进行一些通用东西的初始化"""
    if not os.path.exists('log'):
        os.mkdir('log')
    app = FastAPI()
    app.add_middleware( # 允许跨域第一版
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        ContentSizeLimitMiddleware, 
        max_content_size=static.content_size_limit)

    async def content_size_exceeded_handler(request: Request, exc: HTTPException):
        """特判ContentSizeExceeded，改成413错误，然后其它照旧走默认处理"""
        if isinstance(getattr(exc, '__context__', None), ContentSizeExceeded):
            logger.warning(f'{request.client} {exc.__context__}')
            return JSONResponse({'detail': str(exc.__context__)}, status_code=413)
        return (await http_exception_handler(request, exc))

    # 不能用Exception来抓错，会被FastAPI默认提供的HTTPException抢先抓到
    app.add_exception_handler(400, content_size_exceeded_handler)
    # 按需用，允许任意跨站，在有认证令牌登录的情况下
    @app.middleware('http') # TODO: [insecure] set to a fixed origin
    async def cors_everywhere(request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = request.headers.get('origin', '*')
        return response

    from router import v1_router
    app.include_router(v1_router)

    
    return app

app = preload()

if __name__ == "__main__":
    uvicorn.run(app, **static.site_server_config)