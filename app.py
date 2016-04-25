# -*- coding: utf-8 -*-
import os
import urllib
import json
import time
import requests

from flask import Flask, request, abort, render_template
from tuling123 import robot

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import *
from wechatpy.fields import *

app = Flask(__name__)

default_text = '''功能包括：聊天、笑话、图片、天气、问答、百科、故事、新闻、菜谱、星座、凶吉、成语接龙、快递、飞机、列车、计算

你可以这样问他：
讲笑话
明天天气
查快递
看新闻
刘德华是谁
范冰冰照片
你是傻逼吗
...'''

TOKEN = 'weaming'
AES_KEY = 'zUHZhry09mQb8MRj5AeND9g4lP8DIIoNTnNFTvPY9s0'
APPID = 'wx9600acf68d695dee'
APPSECRET = '2b65f098c41a17903280db9fca15b814'

AMAP_KEY = '53582398c59bb80636f4070760d9f8c0'

keyword_cache = {}

@app.route('/')
def index():
    host = request.url_root
    return render_template('index.html', host=host)

def amap_text_query(keywords, text, loc='深圳'):
    amap_search_api = 'http://restapi.amap.com/v3/place/text?'
    data = urllib.urlencode({
        'key': AMAP_KEY,
        'city': loc,
        'keywords': keywords,
    })
    rt = requests.get(amap_search_api + data)
    rt_text = rt.text.encode('utf-8')
    js = json.loads(rt_text)

    info = ''
    limit = 10
    for index,i in enumerate(js['pois']):
        if index < limit:
            info += str(index+1) + '.'
            info += i['name'].encode('utf-8') + '\n'
            info += i['address'].encode('utf-8') + '\n'
            if type(i['tel']) in [str, unicode]:
                info += i['tel'].encode('utf-8') + '\n'
            info += '-' * 40 + '\n'
    text += info
    return text

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():

    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    encrypt_type = request.args.get('encrypt_type', 'raw')
    msg_signature = request.args.get('msg_signature', '')
    xml = request.data

    # 验证
    try:
        check_signature(TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        abort(403)
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        return echo_str

    # POST request
    if encrypt_type != 'aes':
        # plaintext mode
        msg = parse_message(xml)
        # id  消息 id, 64 位整型。
        # source  消息的来源用户，即发送消息的用户。
        # target  消息的目标用户。
        # create_time 消息的发送时间，UNIX 时间戳
        # type    消息的类型

        if msg.type == 'text':
            if msg.content.startswith('#'):
                if msg.content[1:] == 'send':
                    rt = requests.get('http://api.wowapi.org/faduanxin/')
                    text = rt.text
                else:
                    text = 'input error'
            elif msg.content in ['help', u'帮助']:
                text = default_text
            else:
                content = msg.content                   # 对应于 XML 中的 Content

                if content in ['help', u'帮助']:
                    text = default_text
                elif content.startswith(u'查'):
                    keywords = content[1:].encode('utf-8')
                    if '附近' in keywords or '周边' in keywords or '周围' in keywords:
                        try:
                            tmp = keyword_cache[msg.source]
                        except:
                            tmp = keyword_cache[msg.source] = {}
                            
                        tmp['keywords'] = keywords
                        tmp['ktime'] = time.time()

                        try:
                            tmp = keyword_cache[msg.source]
                            text0 = '已根据您历史位置通过高德地图API找到如下信息：\n\n'
                            if time.time() - tmp['ltime'] < 60 * 15:
                                addr_street = tmp['street']
                                addr_city = tmp['city']
                                text = amap_text_query(addr_street + keywords, text0, addr_city)
                            else:
                                text = '请重新发送您的地理位置！'
                        except:
                            text = '请发送您的地理位置！'
                    else:
                        text0 = '已通过高德地图API为您查找到 深圳 市内所有相关信息：\n\n'
                        text = amap_text_query(keywords, text0)
                else:
                    # text = robot(content, msg.source[:10]) #取消息来源前10位，因为不允许特殊符号

                    tl = robot(content, msg.source[:10], raw=True)
                    # 判断消息类型
                    if tl['code']==100000: #文字
                        text = tl['text']
                    elif tl['code']==200000: #链接
                        text = tl['text']+'\n'+tl['url']
                    elif tl['code']==302000: #新闻
                        text = tl['text']+'\n\n'
                        li = []
                        for i in tl['list']:
                            di = {
                                'title': i['article'],
                                'image': request.url_root + 'static/netease_news.gif',
                                'url': i['detailurl'],
                            }
                            li.append(di)
                        reply = ArticlesReply(message=msg, articles=li)
                        return reply.render()

                    elif tl['code']==308000: #菜谱
                        text = tl['text']+'\n\n'
                        max_item = 5
                        for index,i in enumerate(tl['list']):
                            if index < max_item:
                                text = text + i['name'] + ':\n' + i['info'] + '\n' + i['detailurl']
                                if index < max_item-1:
                                    text += '\n\n'
                    elif tl['code']==305000: #列车
                        text = tl['text']+'\n\n'
                        lenth = len(tl['list'])
                        for index,i in enumerate(tl['list']):
                            text = text + i['trainnum'] + ':\n' + i['start'] + '-->' + i['terminal'] + '\n' + i['starttime'] + '--' + i['endtime']
                            if i['detailurl']:
                                text += '\n' + i['detailurl']
                            if index < lenth-1:
                                text += '\n\n'
                    else:
                        text = 'error'

            text = text.strip()
            reply = TextReply(content=text, message=msg)
        elif msg.type == 'event':
            if msg.event == 'subscribe':
                text0 = '小Q等您很久了，快来调戏我吧！回复【帮助】获取使用指南！'
                reply = create_reply(text0, msg)
        elif msg.type == 'location':
            locate = [msg.location_y, msg.location_x, msg.scale] # 经度，纬度，缩放
            amap_regeo_api = 'http://restapi.amap.com/v3/geocode/regeo?'
            data = urllib.urlencode({
                'key': AMAP_KEY,
                'location': ','.join(locate[:2]),
                'radius': 2000,
                'homeorcorp': 1,
            })
            url = amap_regeo_api + data
            rt = requests.get(url)
            if rt.status_code == 200:
                rt_text = rt.text.encode('utf-8')
                js = json.loads(rt_text)

                addr_full = js['regeocode']['formatted_address'].encode('utf-8')
                addr_street = js['regeocode']['addressComponent']['streetNumber']['street'].encode('utf-8')
                addr_number = js['regeocode']['addressComponent']['streetNumber']['number'].encode('utf-8')
                addr_city = js['regeocode']['addressComponent']['city'].encode('utf-8')

                try:
                    tmp = keyword_cache[msg.source]
                    tmp['street'] = addr_street
                    tmp['city'] = addr_city
                    tmp['ltime'] = time.time()
                except:
                    tmp = None
                if tmp and time.time() - tmp['ktime'] < 60 * 60:
                    text0 = '已根据您位置通过高德地图API找到如下信息：\n\n'
                    text = amap_text_query(addr_street + keyword_cache[msg.source]['keywords'], text0, addr_city)
                else:
                    text = ','.join([addr_full, addr_street, addr_number])
            else:
                text = ', '.join(locate)

            text = text.strip()
            reply = TextReply(content=text, message=msg)
        else:
            reply = create_reply('Sorry, can not handle this for now', msg)
        return reply.render()
    else:
        # encryption mode
        crypto = WeChatCrypto(TOKEN, AES_KEY, APPID)
        try:
            decrypted_xml = crypto.decrypt_message(xml, msg_signature, timestamp, nonce)
        except (InvalidAppIdException, InvalidSignatureException):
            abort(403)
        msg = parse_message(decrypted_xml)

        if msg.type == 'text':
            reply = create_reply(msg.content, msg)
        else:
            reply = create_reply('Sorry, can not handle this for now', msg)
        return crypto.encrypt_message(reply.render(), nonce, timestamp)


if __name__ == '__main__':
    app.run('127.0.0.1', 8001, debug=True)
