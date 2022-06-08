"""读取全局设置文件的模块

计划同时支持env文件和yml文件，后者优先
"""

import yaml
from utility.jsondict import JsonDict
import uvicorn

class static: # 可公开的首选项配置
    # uvicorn api:app 0.0.0.0 65472 --reload --workers=4
    site_server_config = dict(
    # uvicorn.Config( # 不建议用这个起服务，建议命令台打

    
        # app='api:app',
        host='0.0.0.0',
        port=65472,
        debug=True,
        # ssl_certfile='ssl/A.crt', # 本地调试用自签证书
        # ssl_keyfile='ssl/A.key',
        # reload=True, # 这个选项不用uvicorn启动没用
        # workers=4, # 在有有效的迁移方案前先保持单进程运行，大概也够用
        # 要不以后整个服务读写分离吧，写api单线程，与judger交互
    )
    perpage_limit = 50 # 分页元素个数最大限制
    
    content_size_limit = 1024 * 1024 * 1024 # 每个请求体（包括上传文件）的大小限制，这里是1G

    gridfs_chunk_size = 261120 # GridFS中一个分块的大小，这里取默认的255kb

with open('secret.yml', 'r', newline='\n', encoding='utf-8') as f:
    secret = JsonDict(yaml.safe_load(f)) # 包含敏感数据的配置