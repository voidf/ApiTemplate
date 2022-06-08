from loguru import logger
from mongoengine import *
from typing import Optional, TypeVar, Union, get_type_hints
import datetime
from mongoengine.fields import *
from mongoengine.pymongo_support import *
from mongoengine.context_managers import *
from mongoengine.document import *

INVISIBLE = TypeVar('INVISIBLE')

class Chkable():
    """get_or_create的功能Mixin类"""
    @classmethod
    def chk(cls, pk):
        """确保对象存在，如不存在则创建一个，返回给定主键确定的对象"""
        if isinstance(pk, cls):
            return pk
        tmp = cls.objects(pk=pk).first()
        if not tmp:
            # logger.warning(f'creating {tmp}')
            return cls(pk=pk).save()
        return tmp
    @classmethod
    def trychk(cls, pk):
        """若对象存在，返回主键对应的对象，否则返回None"""
        if isinstance(pk, cls):
            return pk
        tmp = cls.objects(pk=pk).first()
        if not tmp:
            return None
        return tmp

