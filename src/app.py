import os

from sanic import Sanic
from sanic.response import file_stream
from xxhash_cffi import xxh32_hexdigest
import aiofiles

from src.sanic_motor import BaseModel
from src.auth import user_authorized
from src.bps import COMMON_API

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONGODB_URI = os.environ.get('MONGODB_HOST', 'mongodb://127.0.0.1:27017/collectors')
BASE_URL = 'http://127.0.0.1:7000'


App = Sanic('collectors')
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
    return await file_stream('html/home.html')



@App.route('/old/home/')
async def cards_page(request):
    return await file_stream('html/backup/index.html')


@App.route('/onepage/create/')
async def programmer_page(request):
    return await file_stream('html/onepage/create.html')


@App.route('/onepage/programmer/')
async def programmer_page(request):
    return await file_stream('html/backup/programmer.html')


@App.route('/onepage/designer/')
async def designer_page(request):
    return await file_stream('html/backup/designer.html')


@App.route('/account/create')
@user_authorized()
async def index_page(request):
    return await file_stream('html/backup/create.html')


@App.route('/login/')
async def tags_page(request):
    return await file_stream('html/backup/login.html')


@App.route('/account/tags/')
@user_authorized()
async def tags_page(request):
    return await file_stream('html/backup/tags.html')


@App.route('/account/category/')
@user_authorized()
async def tags_page(request):
    return await file_stream('html/backup/category.html')


@App.route('/cards/detail/')
async def card_detail_page(request):
    return await file_stream('html/backup/card_detail.html')


@App.route('/cards/')
async def cards_page(request):
    return await file_stream('html/backup/cards.html')


@App.route('/account/list/')
async def list_page(request):
    return await file_stream('html/backup/list.html')


@App.route('/onepage/')
async def onepage_page(request):
    return await file_stream('html/onepage/index.html')


@App.route('/onepage/all/')
async def onepage_all_page(request):
    return await file_stream('html/onepage/all.html')


@App.route('/onepage/demo/')
async def onepage_demo_page(request):
    return await file_stream('html/onepage/demo.html')


@App.route('/onepage/edit/')
async def onepage_edit_page(request):
    return await file_stream('html/onepage/edit.html')


@App.route('/onepage/category/')
async def onepage_category_page(request):
    return await file_stream('html/onepage/category.html')


@App.route('/onepage/detail/')
async def onepage_detail_page(request):
    return await file_stream('html/onepage/detail.html')


@App.route('/domainsite/')
async def domainsite_page(request):
    return await file_stream('html/domainsite/index.html')


@App.route('/domainsite/create/')
async def domainsite_create_page(request):
    return await file_stream('html/domainsite/create.html')


@App.route('/about/')
async def about_page(request):
    return await file_stream('html/about.html')
