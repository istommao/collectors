import os
import time

from urllib.parse import urlparse

import aiohttp
import asyncio
from bs4 import BeautifulSoup

from sanic import Sanic
from sanic.response import json, file_stream
from xxhash_cffi import xxh32_hexdigest
import aiofiles

from src.sanic_motor import BaseModel
from src.models import Item, WebSite, Tag, Category

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONGODB_URI = os.environ.get('MONGODB_HOST', 'mongodb://127.0.01:27017/collectors')
BASE_URL = 'http://127.0.0.1:7000'


async def fetch(session, url):
    headers = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

    async with session.get(url, headers=headers) as response:
        return await response.text()


async def get_url_title(url):
    async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:
        html_content = await fetch(session, url)
        soup = BeautifulSoup(html_content, 'lxml')
        try:
            title = soup.title.text
        except AttributeError:
            title = ''

        return title


async def get_unix_time():
    return int(time.time())


def get_domain_by_url(url):
    x = urlparse(url)
    return x.hostname


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

@App.route('/tags/')
async def tags_page(request):
    return await file_stream('html/tags.html')


@App.route('/category/')
async def tags_page(request):
    return await file_stream('html/category.html')


@App.route('/cards/')
async def cards_page(request):
    return await file_stream('html/cards.html')


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def do_create_item(payload):
    name = payload['name']
    category = payload['category']
    url = payload['url']
    desc = payload['desc']
    tags = payload['tags']

    result = await Item.insert_one({
        'name': name,
        'category': category,
        'url': url,
        'desc': desc,
        'tags': tags,
        'create_at': await get_unix_time()
    })
    return result


@App.route('/api/items/', methods=['POST'])
async def do_create_item_api(request):
    category = request.form.get('category')
    name = request.form.get('name', '')
    content = request.form.get('content')
    desc = request.form.get('desc', '')

    try:
        tags = request.form['tags']
    except KeyError:
        tags = []

    url = content
    # url = content if category == 'website' else ''
    # if url:
    name = await get_url_title(url)
    desc = name

    item = await Item.find_one({'content': content})
    if item:
        return json({'message': '已创建'}) 
    else:
        payload = {
            'name': name,
            'desc': desc,
            'content': content,
            'url': url,
            'tags': tags,
            'category': category
        }
        await do_create_item(payload)

        if url:
            domain = get_domain_by_url(url)
            site = await WebSite.find_one({'domain': domain})
            if not site:
                await WebSite.insert_one({'name': domain, 'domain': domain})

        return json({'message': '创建成功'})


@App.route('/api/items/')
async def item_list_api(request):
    qs = await Item.find(
        {}, sort='create_at desc'
    )
    datalist = []

    for obj in qs.objects:
        item = {
            'url': obj['url'],
            'category': obj['category'],
            'name': obj['name'],
            'tags': obj['tags'],
            'create_at': obj['create_at']
        }
        datalist.append(item)

    return json({'data': datalist, 'code': 0})


@App.route('/api/category/', methods=['GET'])
async def category_list_api(request):
    qs = await Category.find({})
    datalist = []

    for obj in qs.objects:
        item = {
            'attribute': obj['attribute'],
            'name': obj['name']
        }
        datalist.append(item)

    return json({'data': datalist, 'code': 0})


@App.route('/api/category/', methods=['POST'])
async def do_create_category_api(request):
    attribute = request.form.get('attribute')
    name = request.form.get('name')

    tag = await Category.find_one({'attribute': attribute, 'name': name})

    if not tag:
        tag = await Category.insert_one({
            'name': name,
            'attribute': attribute
        })

    return json({'message': '创建成功'})


@App.route('/api/tags/', methods=['GET'])
async def tag_list_api(request):
    qs = await Tag.find(
        {}, sort='create_at desc'
    )
    datalist = []

    for obj in qs.objects:
        item = {
            'attribute': obj['attribute'],
            'name': obj['name']
        }
        datalist.append(item)

    return json({'data': datalist, 'code': 0})


@App.route('/api/tags/', methods=['POST'])
async def do_create_tags_api(request):
    attribute = request.form.get('attribute')
    name = request.form.get('name')

    tag = await Tag.find_one({'attribute': attribute, 'name': name})

    if not tag:
        tag = await Tag.insert_one({
            'name': name,
            'attribute': attribute
        })

    return json({'message': '创建成功'})
