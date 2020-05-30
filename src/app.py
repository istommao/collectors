import os
import time

from sanic import Sanic
from sanic.response import json, file_stream
from xxhash_cffi import xxh32_hexdigest
import aiofiles

from src.sanic_motor import BaseModel
from src.models import Item

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONGODB_URI = os.environ.get('MONGODB_HOST', 'mongodb://127.0.01:27017/filebed')
BASE_URL = 'http://127.0.0.1:7000'


async def get_unix_time():
    return int(time.time())


App = Sanic('filebed')

App.config.update(
    {
        # Motor config
        'MOTOR_URI': MONGODB_URI,
        'LOGO': None,
    }
)


BaseModel.init_app(App)

# 提供文件夹`static`里面的文件到URL `/static`的访问。
App.static('/static', BASE_DIR + '/static')
App.static('/upload', BASE_DIR + '/upload')

BASE_UPLOAD_FOLDER = 'upload'


@App.route('/')
async def index_page(request):
    return await file_stream('html/create.html')


@App.route('/cards/')
async def cards_page(request):
    return await file_stream('html/cards.html')


@App.route('/api/items/')
async def item_list_api(request):
    qs = await Item.find(
        {}, sort='create_at desc'
    )
    datalist = []

    for obj in qs.objects:
        item = {
            'url': obj['url'],
            'type': obj['type'],
            'name': obj['name'],
            'create_at': obj['create_at']
        }
        datalist.append(item)

    return json({'data': datalist, 'code': 0})
