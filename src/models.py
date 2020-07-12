from .sanic_motor import BaseModel


class Category(BaseModel):
    __coll__ = 'Categorys'
    # name:str 名称
    # attribute:str 属性 website/app/goods


class Item(BaseModel):
    __coll__ = 'Items'
    # name:str 名称
    # category:str 分类
    # desc:str 内容描述
    # image:str 封面图片
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
    # attribute:str 类型 website/app/goods


class ItemImage(BaseModel):
    __coll__ = 'ItemImages'
    # name:str 名称
    # path: path
    # create_at:int Unix时间戳

"""OnePage block"""


class SiteItem(BaseModel):
    __coll__ = 'SietItems'
    # name:str 名称
    # category:str 名称
    # link: 链接
    # desc:str 内容描述
    # image:str 封面图片


class SiteCategory(BaseModel):
    __coll__ = 'SiteCategorys'
    # name:str 名称
    # image:str 封面图片
    # desc:str 内容描述


"""Domain block 按领域划分的站点"""


class Domain(BaseModel):
    __coll__ = 'Domain'
    # name:str 名称
    # image:str 封面图片
    # desc:str 内容描述


class DomainSite(BaseModel):
    """按领域划分."""
    __coll__ = 'DomainSites'

    # name:str 名称
    # image:str 封面图片
    # desc:str 内容描述
    # link: 链接
    # category:str 名称

    # domain:str domain
