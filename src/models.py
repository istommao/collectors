from .sanic_motor import BaseModel


class Item(BaseModel):
    __coll__ = 'Items'
    # name:str 名称
    # type:str 类型
    # desc:str 内容描述
    # url:str 链接
    # tags:list<str> 标签
    # create_at:int Unix时间戳


class WebSite(BaseModel):
    __coll__ = 'WebSites'
    # name:str 名称
    # domain:str domain


class Tag(BaseModel):
    __coll__ = 'Tags'
    # name:str 名称
    # type:str 类型 website/app/goods
