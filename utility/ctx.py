import contextvars
import types
request_global = contextvars.ContextVar("request_global", default=types.SimpleNamespace())
"""这是生命周期为一次请求的上下文安全全局变量空间g()
目前主要用来放登录用户，即g().user"""
def g(): return request_global.get()