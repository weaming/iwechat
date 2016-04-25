# -*- coding: utf-8 -*-
import os
import urllib
import json
import requests

from flask import Flask, request, abort, render_template
from tuling123 import robot

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.replies import *

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

@app.route('/')
def index():
    host = request.url_root
    return render_template('index.html', host=host)

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
                    text = '已通过高德地图API为您查找到信息：\n\n'
                    amap_search_api = 'http://restapi.amap.com/v3/place/text?key=' + AMAP_KEY + '&'
                    data = urllib.urlencode({
                        'city': '深圳',
                        'keywords': content[1:].encode('utf-8'),
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
                            info += i['tel'].encode('utf-8') + '\n'
                            info += '-' * 40 + '\n'
                    text += info
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
        elif msg.type =='event':
            if msg.event == 'subscribe':
                text = '小Q等您很久了，快来调戏我吧！回复【帮助】获取使用指南！'
                reply = create_reply(text, msg)
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
