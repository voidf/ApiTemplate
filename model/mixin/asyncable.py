from fastapi import HTTPException
from inspect import isfunction
from loguru import logger
from typing import Optional, TypeVar, Union, get_type_hints
import datetime

from mongoengine.errors import ValidationError
from utility.motor import db
from pymongo import ReturnDocument
import motor
import types
# import sys

def result2bool(result):
    """令一个查询结果的布尔值返回存不存在匹配的文档，注意不是有没有修改"""
    # https://stackoverflow.com/questions/48448074/adding-a-property-to-an-existing-object-instance
    # https://stackoverflow.com/questions/3308792/python-object-layout
    # print('before', sys.getsizeof(result))
    class_name = result.__class__.__name__ + 'Boolean'
    child_class = type(class_name, (result.__class__,), {
        '__slots__' : tuple(),
        '__bool__': lambda self: self.raw_result['n'] > 0
    })
    result.__class__ = child_class
    return result

class Asyncable:
    """方便一些的对接motor的工具类"""

    @classmethod
    def convert_pk(cls, pk):
        return getattr(cls, cls._reverse_db_field_map['_id']).to_mongo(pk)

    @classmethod
    def _aget_collection(cls) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return db[cls._get_collection_name()]

    @classmethod
    def _to_mongoengine(cls, instance_dict: dict, created=True):
        ins = cls._from_son(instance_dict, created=created, _auto_dereference=False)
        return ins

    @classmethod
    def _nullable(cls, may_null_instance, created=True):
        """内部使用的要么返回一个这个实例要么返回None"""
        return None if may_null_instance is None else cls._to_mongoengine(may_null_instance, created=created)

    

    @classmethod
    async def aaggregate_list(cls, *args, **kwargs):
        """调用本集合的aggregate方法，返回一系列操作的结果"""
        return (await cls._aget_collection().aggregate(*args, **kwargs).to_list(length=None))
    
    @classmethod
    async def acount(cls, *args, **kwargs):
        """调用本集合的count_documents方法，返回满足条件的结果数"""
        return (await cls._aget_collection().count_documents(*args, **kwargs))
    
    @classmethod
    async def afind(cls, *args, **kwargs):
        """调用本集合的find方法，把一系列结果打包成Document的实例表"""
        return [cls._to_mongoengine(i, created=False) for i in 
        (await cls._aget_collection().find(*args, **kwargs).to_list(length=None))]
    
    @classmethod
    async def afind_one(cls, *args, **kwargs):
        """调用本集合的find_one方法，把结果打包成Document的实例"""
        return cls._nullable(await cls._aget_collection().find_one(*args, **kwargs), created=False)
    
    @classmethod
    async def aupdate_one(cls, *args, **kwargs):
        """调用本集合的update_one方法，返回一个UpdateResult"""
        return result2bool(await cls._aget_collection().update_one(*args, **kwargs))
    
    @classmethod
    async def aupd(cls, pk, **kwargs):
        """更新给定主键的文档，返回一个UpdateResult"""
        return result2bool(await cls._aget_collection().update_one({'_id': cls.convert_pk(pk)}, {'$set':kwargs}))
    
    @classmethod
    async def armrf(cls, *args, **kwargs):
        """清空一个collection， 起名源于rm -rf"""
        return (await cls._aget_collection().delete_many({}, *args, **kwargs))

    @classmethod
    async def atrychk(cls, pk, *args, **kwargs):
        """用主键尝试找一个文档"""
        return cls._nullable(await cls._aget_collection().find_one({'_id': cls.convert_pk(pk)}, *args, **kwargs), created=False)

    @classmethod
    async def achk(cls, pk, *args, **kwargs):
        """1RTT令给定的主键的文档保证存在，不存在会塞入一个默认文档"""
        default_document = cls().to_mongo()
        res = await cls._aget_collection().find_one_and_update(
            {'_id': cls.convert_pk(pk)},
            {'$setOnInsert': default_document},
            *args,
            upsert=True,
            return_document=ReturnDocument.AFTER,
            **kwargs
        )

        return cls._to_mongoengine(res, created=False)

    @classmethod
    async def aunchk(cls, pk, *args, **kwargs):
        """根据主键删一个文档"""
        return result2bool(await cls._aget_collection().delete_one({'_id': cls.convert_pk(pk)}, *args, **kwargs))

    
    @classmethod
    async def apop(cls, pk, *args, **kwargs):
        """根据主键删一个文档，并返回它"""
        return cls._nullable(await cls._aget_collection().find_one_and_delete({'_id': cls.convert_pk(pk)}, *args, **kwargs))

    @classmethod
    async def amock(cls, pk, *args, **kwargs) -> dict:
        """在数据库中查找给定主键的文档，如果有则返回其本身补全default值之后的文档，
        没有则返回default文档，不会修改数据库，1RTT
        
        可以使用projection之类的查询参数，会被转发给find_one"""
        res = await cls._aget_collection().find_one(
            {'_id': cls.convert_pk(pk)}, *args, **kwargs
        )
        if not res:
            res = {'_id': cls.convert_pk(pk)}
        return cls._to_mongoengine(res)

    @classmethod
    async def aensure(cls, pk):
        """找到了更好的写法，不再需要5.2或以上

        通过返回UpdateResult的raw_result.upserted存不存在判断有没有插入，直接转换bool总是True
        
        ~~确保给定主键的文档存在于数据库中，如不存在则塞入一个含默认字段的对象，没有返回值，1RTT。
        要求MongoDB Server 5.2或以上，截至写此语句时5.2仍是dev版本~~"""
        default_document = cls().to_mongo()
        return result2bool(await 
            cls._aget_collection()
            .update_one(
                {'_id': cls.convert_pk(pk)},
                {'$setOnInsert': default_document},
                upsert=True
            )
        )

    async def adestroy(self, *args, **kwargs):
        """删掉自己"""
        return (await self.aunchk(self.pk, *args, **kwargs))

    async def asave_report_error(self, *args, **kwargs):
        try:
            return (await self.asave(*args, **kwargs))
        except ValidationError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def asave(
        self,
        force_insert=False, 
        validate=True,
        clean=True, **kwargs):
        """异步阉割版的.save功能，应该只会保存已经修改的field，支持投影但是缺少测试"""
        if validate:
            self.validate(clean=clean)

        doc_id = self.to_mongo(fields=[self._meta["id_field"]])
        created = "_id" not in doc_id or self._created or force_insert

        doc = self.to_mongo()

        if created:
            object_id = await self._asave_create(doc, force_insert)
        else:
            object_id, created = await self._asave_update(doc)
        # else:
            # await self._aget_collection().update_one({'_id': doc['_id']}, {'$set':doc}, upsert=True, **kwargs)
        
        id_field = self._meta["id_field"]
        if created or id_field not in self._meta.get("shard_key", []):
            self[id_field] = self._fields[id_field].to_python(object_id)
        self._clear_changed_fields()
        self._created = False

        return self

    async def _asave_create(self, doc, force_insert):
        """直接抄MongoEngine的
        
        Save a new document.

        Helper method, should only be used inside save().
        """
        collection = self._aget_collection()
        if force_insert:
            return (await collection.insert_one(doc)).inserted_id
        # insert_one will provoke UniqueError alongside save does not
        # therefore, it need to catch and call replace_one.
        if "_id" in doc:
            select_dict = {"_id": doc["_id"]}
            select_dict = self._integrate_shard_key(doc, select_dict)
            raw_object = await collection.find_one_and_replace(select_dict, doc)
            if raw_object:
                return doc["_id"]

        object_id = (await collection.insert_one(doc)).inserted_id

        return object_id

    async def _asave_update(self, doc):
        """直接抄MongoEngine的
        
        Update an existing document.

        Helper method, should only be used inside save().
        """
        collection = self._aget_collection()
        object_id = doc["_id"]
        created = False

        select_dict = {}
        select_dict["_id"] = object_id

        select_dict = self._integrate_shard_key(doc, select_dict)

        update_doc = self._get_update_doc()
        if update_doc:
            upsert = True
            
            last_error = (await collection.update_one(
                select_dict, update_doc, upsert=upsert
            )).raw_result
            if not upsert and last_error["n"] == 0:
                raise Exception(
                    "Race condition preventing document update detected"
                )
            if last_error is not None:
                updated_existing = last_error.get("updatedExisting")
                if updated_existing is False:
                    created = True
                    # !!! This is bad, means we accidentally created a new,
                    # potentially corrupted document. See
                    # https://github.com/MongoEngine/mongoengine/issues/564

        return object_id, created