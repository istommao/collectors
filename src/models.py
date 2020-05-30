from .sanic_motor import BaseModel


class Item(BaseModel):
    __coll__ = 'Items'
    # name:str
    # type:str
    # url:str
    # create_at:int Unix时间戳

