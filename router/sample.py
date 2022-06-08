from fastapi import APIRouter

sample_router = APIRouter(
    prefix="/sample",
    tags=["Sample | 示例接口"],
    dependencies=[]
)

@sample_router.post('/test')
async def atester():
    return {'Are U': 'OK?'}