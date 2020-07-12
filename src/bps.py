import os
import time
from urllib.parse import urlparse

import itertools
import operator

from sanic import Blueprint
from sanic.response import json

from bson.objectid import ObjectId

import aiohttp
import asyncio
import aiofiles

from xxhash_cffi import xxh32_hexdigest

from bs4 import BeautifulSoup

from src.models import (
    Item, WebSite, Tag, Category, ItemImage, SiteItem, SiteCategory,
    DomainSite
)


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
    image = payload['image']

    result = await Item.insert_one({
        'name': name,
        'category': category,
        'url': url,
        'desc': desc,
        'tags': tags,
        'image': image,
        'create_at': await get_unix_time()
    })
    return result


@COMMON_API.route('/items/', methods=['POST'])
async def do_create_item_api(request):
    category = request.form.get('category')
    name = request.form.get('name', '')
    content = request.form.get('content')
    desc = request.form.get('desc', '')
    image = request.form.get('image', '')

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
            'category': category,
            'image': image
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
            'uid': str(obj['_id']),
            'url': obj['url'],
            'category': obj['category'],
            'name': obj['name'],
            'image': obj['image'],
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


async def write_file(path, body):

    async with aiofiles.open(path, 'wb') as f:
        await f.write(body)
    f.close()


BASE_UPLOAD_FOLDER = 'upload'


@COMMON_API.route('/upload', methods=['POST'])
async def upload_api(request):
    upload_file = request.files.get('file')
    name = upload_file.name

    folder_path = '{}/{}'.format(
        BASE_UPLOAD_FOLDER,
        str(int(time.time()))
    )

    file_ext = 'jpg'
    file_path = '{}/{}'.format(folder_path, xxh32_hexdigest(name).decode('utf-8') + '.{}'.format(file_ext))

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    await write_file(file_path, upload_file.body)

    result = await ItemImage.insert_one({
        'name': name,
        'path': file_path,
        'create_at': await get_unix_time(),
    })

    return json({'url': '/' + file_path})



@COMMON_API.route('/items/<uid:string>/', methods=['GET'])
async def item_detail_api(request, uid):

    obj = await Item.find_one(
        {'_id': ObjectId(uid)}
    )

    item = {
        'uid': str(obj['_id']),
        'url': obj['url'],
        'category': obj['category'],
        'name': obj['name'],
        'image': obj['image'],
        'tags': obj['tags'],
        'create_at': obj['create_at']
    }

    return json({'data': item, 'code': 0})


@COMMON_API.route('/items/<uid:string>/', methods=['POST'])
async def do_update_item_api(request, uid):
    image = request.form.get('image', '')
    image = request.form.get('image', '')

    item = await Item.find_one({'_id': ObjectId(uid)})
    if not item:
        return json({'message': '不存在的记录'}) 
    else:
        payload = {
            'image': image
        }
        await Item.update_one({'_id': ObjectId(uid)}, {'$set': payload})

        return json({'message': '修改成功'})


async def do_create_siteitem(payload):
    name = payload['name']
    link = payload['link']
    desc = payload['desc']
    image = payload['image']
    category = payload['category']

    result = await SiteItem.insert_one({
        'name': name,
        'link': link,
        'desc': desc,
        'category': category,
        'image': image
    })
    return result


@COMMON_API.route('/onepage/', methods=['GET'])
async def get_onepage_list_api(request):
    category = request.args.get('category', '')
    query_condition = {}
    if category:
        query_condition = {'category': category}

    qs = await SiteItem.find(query_condition)
    datalist = []

    for obj in qs.objects:
        item = {
            'name': obj['name'],
            'link': obj['link'],
            'category': obj['category'],
            'image': obj['image'],
            'desc': obj['desc'],
        }
        datalist.append(item)

    datalist = itertools.groupby(
        sorted(datalist, key=operator.itemgetter('category')),
        key=operator.itemgetter('category')
    )
    datalist = [{'name': key, 'datalist': list(group)} for key, group in datalist if key]

    total_count = await SiteItem.count({})
    total_category = await SiteCategory.count({})

    return json({'datalist': datalist, 'code': 0,
                 'total_count': total_count, 'total_category': total_category})


@COMMON_API.route('/onepage/', methods=['POST'])
async def do_create_onepage_api(request):
    name = request.form.get('name', '')
    category = request.form.get('category', '')
    link = request.form.get('link')
    desc = request.form.get('desc', '')
    image = request.form.get('image', '')

    item = await SiteItem.find_one({'link': link})
    if item:
        return json({'message': '已创建'}) 
    else:
        payload = {
            'name': name,
            'desc': desc,
            'link': link,
            'category': category,
            'image': image
        }
        await do_create_siteitem(payload)

        domain = get_domain_by_url(link)
        site = await WebSite.find_one({'domain': domain})
        if not site:
            await WebSite.insert_one({'name': domain, 'domain': domain})

        return json({'message': '创建成功'})



@COMMON_API.route('/onepage/all/', methods=['GET'])
async def all_onepage_api(request):
    qs = await SiteItem.find({})
    datalist = []

    for obj in qs.objects:
        item = {
            'name': obj['name'],
            'link': obj['link'],
            'image': obj['image'],
            'desc': obj['desc'],
        }
        datalist.append(item)

    return json({'datalist': datalist, 'code': 0})


async def do_create_site_category(payload):
    name = payload['name']
    desc = payload['desc']
    image = payload['image']

    result = await SiteCategory.insert_one({
        'name': name,
        'desc': desc,
        'image': image
    })
    return result


@COMMON_API.route('/onepage/category/', methods=['POST'])
async def do_create_onepage_api(request):
    name = request.form.get('name', '')
    desc = request.form.get('desc', '')
    image = request.form.get('image', '')

    item = await SiteCategory.find_one({'name': name})
    if item:
        return json({'message': '已创建'}) 
    else:
        payload = {
            'name': name,
            'desc': desc,
            'image': image
        }
        await do_create_site_category(payload)

        return json({'message': '创建成功'})


@COMMON_API.route('/onepage/category/', methods=['GET'])
async def site_category_api(request):
    qs = await SiteCategory.find({})
    datalist = []

    for obj in qs.objects:
        item = {
            'name': obj['name'],
            'image': obj['image'],
            'desc': obj['desc'],
        }
        datalist.append(item)

    return json({'datalist': datalist, 'code': 0})


@COMMON_API.route('/domainsite/', methods=['GET'])
async def get_domainsite_list_api(request):
    name = request.args.get('name', '')
    query_condition = {'domain': name}

    qs = await DomainSite.find(query_condition)
    datalist = []

    for obj in qs.objects:
        item = {
            'name': obj['name'],
            'link': obj['link'],
            'category': obj['category'],
            'image': obj['image'],
            'desc': obj['desc'],
        }
        datalist.append(item)

    datalist = itertools.groupby(
        sorted(datalist, key=operator.itemgetter('category')),
        key=operator.itemgetter('category')
    )
    datalist = [{'name': key, 'datalist': list(group)} for key, group in datalist if key]

    total_count = await DomainSite.count({'domain': name})

    return json({'datalist': datalist, 'code': 0, 'total_count': total_count})


async def do_create_domain_site(payload):
    name = payload['name']
    link = payload['link']
    desc = payload['desc']
    domain = payload['domain']
    image = payload['image']
    category = payload['category']

    result = await DomainSite.insert_one({
        'name': name,
        'link': link,
        'desc': desc,
        'domain': domain,
        'category': category,
        'image': image
    })
    return result


@COMMON_API.route('/domainsite/', methods=['POST'])
async def do_create_domainsite_api(request):
    name = request.form.get('name', '')
    domain = request.form.get('domain', '')
    category = request.form.get('category', '')
    link = request.form.get('link')
    desc = request.form.get('desc', '')
    image = request.form.get('image', '')

    item = await DomainSite.find_one({'link': link})
    if item:
        return json({'message': '已创建'}) 
    else:
        payload = {
            'name': name,
            'desc': desc,
            'link': link,
            'category': category,
            'domain': domain,
            'image': image
        }
        await do_create_domain_site(payload)

        domain = get_domain_by_url(link)
        site = await WebSite.find_one({'domain': domain})
        if not site:
            await WebSite.insert_one({'name': domain, 'domain': domain})

        return json({'message': '创建成功'})
