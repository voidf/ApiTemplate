import os
from fastapi import APIRouter, Depends, FastAPI
from loguru import logger
v1_router = APIRouter(
    prefix="/api/v1",
    tags=["All routers | 所有接口"],
    dependencies=[]
)
from utility.importer import route_importer, route_group_importer

dest_module = __name__.split('.')
logger.debug(dest_module)
route_importer(dest_module, v1_router)
route_group_importer(dest_module, v1_router)
