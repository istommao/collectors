import os
import time

from urllib.parse import urlparse


from sanic import Sanic
from sanic.response import file_stream
from xxhash_cffi import xxh32_hexdigest
import aiofiles

from src.sanic_motor import BaseModel
from src.auth import user_authorized
from src.bps import COMMON_API

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONGODB_URI = os.environ.get('MONGODB_HOST', 'mongodb://127.0.01:27017/collectors')
BASE_URL = 'http://127.0.0.1:7000'


App = Sanic('filebed')
App.blueprint(COMMON_API)

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
async def cards_page(request):
    return await file_stream('html/cards.html')


@App.route('/create')
@user_authorized()
async def index_page(request):
    return await file_stream('html/create.html')


@App.route('/login/')
async def tags_page(request):
    return await file_stream('html/login.html')


@App.route('/tags/')
@user_authorized()
async def tags_page(request):
    return await file_stream('html/tags.html')


@App.route('/category/')
@user_authorized()
async def tags_page(request):
    return await file_stream('html/category.html')


@App.route('/cards/')
async def cards_page(request):
    return await file_stream('html/cards.html')
