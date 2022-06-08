from fastapi import APIRouter
import os
import importlib

from loguru import logger

def route_importer(dest_module: list, father_router: APIRouter):
    for module in os.listdir(os.path.join(os.getcwd(), *dest_module)):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        module = module[:-3]
        package = importlib.import_module(f"{'.'.join(dest_module)}.{module}")
        logger.debug(f'loaded router: {package}')
        router = getattr(package, f"{module}_router")
        father_router.include_router(router)

def route_group_importer(dest_module: list, father_router: APIRouter):
    base = (os.getcwd(), *dest_module)
    for module in os.listdir(os.path.join(*base)):
        if module == '__pycache__' or not os.path.isdir(
            os.path.join(*base, module)
        ):
            continue
        package = importlib.import_module(f"{'.'.join(dest_module)}.{module}")
        logger.debug(f'loaded router: {package}')
        router = getattr(package, f"{module}_route")
        father_router.include_router(router)
