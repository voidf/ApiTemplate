from model.mixin.asyncable import Asyncable
from mongoengine import *
from mongoengine.document import Document
from mongoengine.fields import *
from utility.password import encrypt
from mongoengine.queryset import *

class User(Document, Asyncable):
    """用户主体"""
    # 认证！（字正腔圆）
    handle = StringField(primary_key=True, regex=r'^[0-9a-zA-Z_]+$')
    password = StringField()
    password_reset_key = StringField() # 重设密码的令牌，忘记密码用
    jwt_updated = DateTimeField() # 密码更新时间，令之前的失效

    def pw_chk(self, password: str) -> bool:
        return self.password == encrypt(password)

    def pw_set(self, password: str) -> "User":
        self.password = encrypt(password)
        return self
