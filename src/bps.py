from sanic import Blueprint
from sanic.response import json

import aiohttp
import asyncio

from bs4 import BeautifulSoup

from src.models import Item, WebSite, Tag, Category


COMMON_API = Blueprint('CommonAPI', url_prefix='/api')


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


@COMMON_API.route('/items/', methods=['POST'])
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


def get_page_size(args):
    page_size = args.get('page_size', '20')
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20
    return page_size


def get_current_page(args):
    current_page =  args.get('page', '1')
    try:
        current_page = int(current_page)
    except ValueError:
        current_page = 1
    return current_page


async def get_item_page_data(request):
    current_page = get_current_page(request.args)
    page_size = get_page_size(request.args)

    total_page = await Item.count({})
    pagedata = {
        'total': total_page,
        'page': current_page,
        'page_size': page_size
    }

    return pagedata


@COMMON_API.route('/items/pagedata/')
async def item_pagedata_api(request):
    pagedata = await get_item_page_data(request)

    return json({'data': pagedata})


@COMMON_API.route('/items/')
async def item_list_api(request):
    current_page = get_current_page(request.args)
    page_size = get_page_size(request.args)

    category = request.args.get('category')
    if category:
        query_condition = {'category': category}
    else:
        query_condition = {}

    qs = await Item.find(
        query_condition, sort='create_at desc',
        page=current_page, per_page=page_size
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


@COMMON_API.route('/category/', methods=['GET'])
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


@COMMON_API.route('/category/', methods=['POST'])
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


@COMMON_API.route('/tags/', methods=['GET'])
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


@COMMON_API.route('/tags/', methods=['POST'])
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



@COMMON_API.route('/user/login/', methods=['POST'])
async def login_api(request):
    uid = 'collectors'
    response = json({'message': '登录成功', 'code': 200})
    response.cookies['sessionid'] = uid
    response.cookies['sessionid']['domain'] = '*'
    response.cookies['sessionid']['httponly'] = True

    return response
