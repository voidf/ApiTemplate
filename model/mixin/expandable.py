import json
from mongoengine import *
from typing import Optional, TypeVar, Union, get_type_hints
import datetime
from mongoengine.fields import *
from mongoengine.pymongo_support import *
from mongoengine.context_managers import *
from mongoengine.document import *

INVISIBLE = TypeVar('INVISIBLE')

class Expandable():
    """
    递归地解引用展开Mixin类，不能处理成环情况，与mongoengine.document.Document搭配使用
    
    或者叫自动拼表？
    """
    @staticmethod
    def expand_visible(obj):
        if hasattr(obj, 'get_base_info'):
            return getattr(obj, 'get_base_info')()
        else:
            return obj
    @staticmethod
    def expand_all(obj):
        if hasattr(obj, 'get_all_info'):
            return getattr(obj, 'get_all_info')()
        else:
            return obj

    def get_fields(self) -> dict:
        d = json.loads(self.to_json())
        d['pk'] = d.pop('_id')
        return d

    def get_visible_fields(self) -> dict:
        d = self.get_fields()
        for field_name in self._fields_ordered:
            try:
                if get_type_hints(self).get(field_name, None) == INVISIBLE:
                    d.pop(field_name, None)
            except:
                pass
        return d
        
    def get_base_info(self):
        """不展开带INVISIBLE的field"""
        try:
            d = {}
            for field_name in self._fields_ordered:
                if get_type_hints(self).get(field_name, None) == INVISIBLE:
                    continue
                field = getattr(self, field_name)
                if isinstance(field, list):
                    for i in field:
                        d.setdefault(field_name, []).append(Expandable.expand_visible(i))
                else:
                    d[field_name] = Expandable.expand_visible(field)
            d['pk'] = str(self.pk)
            return d
        except: # 不加注解上面会报错
            return self.get_all_info()
    def get_all_info(self):
        """无视INVISIBLE，展开所有field"""
        d = {} 
        for field_name in self._fields_ordered:
            field = getattr(self, field_name)
            if isinstance(field, list):
                for i in field:
                    d.setdefault(field_name, []).append(Expandable.expand_all(i))
            else:
                d[field_name] = Expandable.expand_all(field)
        d['pk'] = str(self.pk)
        return d


class SaveTimeExpandable(Expandable):
    create_time = DateTimeField()
    def save_changes(self):
        return self.save()
    def first_create(self):
        self.create_time = datetime.datetime.now()
        return self.save_changes()
    
    def get_base_info(self, *args):
        d = super().get_base_info(*args)
        d['create_time'] = self.create_time.strftime('%Y-%m-%d')
        return d

    def get_all_info(self, *args):
        d = super().get_all_info(*args)
        d['create_time'] = self.create_time.strftime('%Y-%m-%d')
        return d
