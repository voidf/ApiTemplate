import datetime
import traceback
from jose import jwt
from loguru import logger
from fastapi import Request, HTTPException

from config import secret
from utility.ctx import g
from model.user import User

def generate_login_jwt(user: User, expires: float=86400,):
    return jwt.encode(
        {
            'user': str(user.pk),
            'born': str(int(datetime.datetime.now().timestamp())), # 颁发令牌的时间
            'ddl': str(int((datetime.datetime.now()+ datetime.timedelta(seconds=expires)).timestamp()))
        },  # payload, 有效载体
        secret.jwt_key,  # 进行加密签名的密钥
    )

async def verify_login_jwt(token):
    """注意这步有数据库1RTT开销，证毕令牌有效性后查询用户是否存在"""
    try:
        payload = jwt.decode(token, secret.jwt_key)
        if datetime.datetime.now().timestamp() > float(payload['ddl']):
            return None, "token expired"
        if not (u := await User.atrychk(payload['user'])):
            return None, "user not exists"
        if u.jwt_updated and u.jwt_updated > payload['born']:
            return None, "token denied"
        return u, ""
    except:
        logger.critical(traceback.format_exc())
        return None, "unexpected error"


async def should_login(auth: Request):
    """请求预处理，将令牌放入线程作用域g()"""
    try:
        logger.debug(auth.client.host)
        
        if Authorization := auth.cookies.get('Authorization', None):
            g().user, g().msg = await verify_login_jwt(Authorization)
            if g().user:
                return g().user
        # TODO: [insecure] remove this
        elif Authorization := auth.headers.get('jwt', None):
            g().user, g().msg = await verify_login_jwt(Authorization)
            if g().user:
                return g().user
    except:
        logger.critical(traceback.format_exc())
        raise HTTPException(400, "data error")
    raise HTTPException(401, "this operation requires login")
