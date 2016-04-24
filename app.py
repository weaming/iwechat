# -*- coding: utf-8 -*-
import os
import requests

from flask import Flask, request, abort, render_template
from tuling123 import robot

from wechat_sdk import WechatConf
from wechat_sdk import WechatBasic
from wechat_sdk.exceptions import ParseError
from wechat_sdk.messages import *

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import (
    InvalidSignatureException,
    InvalidAppIdException,
)

app = Flask(__name__)


@app.route('/')
def index():
    host = request.url_root
    return render_template('index.html', host=host)

@app.route('/wechatsdk', methods=['GET', 'POST'])
def wechatsdk():
    DEBUG = True
    conf = WechatConf(
        token='weaming',
        appid='wx9600acf68d695dee',
        appsecret='2b65f098c41a17903280db9fca15b814',
        encrypt_mode='compatible',  # 可选项：normal/compatible/safe，分别对应于 明文/兼容/安全 模式
        encoding_aes_key='zUHZhry09mQb8MRj5AeND9g4lP8DIIoNTnNFTvPY9s0'  # 如果传入此值则必须保证同时传入 token, appid
    )
    wechat = WechatBasic(conf=conf)

    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echostr = request.args.get('echostr', '')

    if request.method == 'GET':
        if DEBUG or wechat.check_signature(signature, timestamp, nonce):
            echo_str = request.args.get('echostr', '')
            return echo_str

    if request.method == 'POST':
        try:
            wechat.parse_data(request.data)
        except ParseError:
            print 'Invalid Body Text'

        common_id = wechat.message.id          # 对应于 XML 中的 MsgId
        common_target = wechat.message.target  # 对应于 XML 中的 ToUserName
        common_source = wechat.message.source  # 对应于 XML 中的 FromUserName
        common_time = wechat.message.time      # 对应于 XML 中的 CreateTime
        common_type = wechat.message.type      # 对应于 XML 中的 MsgType
        common_raw = wechat.message.raw        # 原始 XML 文本，方便进行其他分析

        if isinstance(wechat.message, TextMessage):
            content = wechat.message.content                   # 对应于 XML 中的 Content

            if content in ['help', u'帮助']:
                text = '''功能包括：聊天、笑话、图片、天气、问答、百科、故事、新闻、菜谱、星座、凶吉、成语接龙、快递、飞机、列车、计算

你可以这样问他：
讲笑话
明天天气
查快递
看新闻
刘德华是谁
范冰冰照片
你是傻逼吗
...
随意聊天，不要太拘谨哦！'''
            elif content.startswith('http'):
                li = []
                di = {
                    'title': content.split('\n')[1],
                    'picurl': 'http://bitsflow.org/favicon.png',
                    'url': content.split('\n')[0],
                }
                li.append(di)
                xml = wechat.response_news(li)
                return xml
            else:
                # text = robot(content, common_source[:10]) #取消息来源前10位，因为不允许特殊符号

                tl = robot(content, common_source[:10], raw=True) #取消息来源前10位，因为不允许特殊符号，返回原始json的dict
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
                            'picurl': request.url_root + 'static/netease_news.gif',
                            'url': i['detailurl'],
                        }
                        li.append(di)
                    xml = wechat.response_news(li)
                    return xml
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

            def myfilter(text):
                if text.endswith('\n'):
                    text = text[:-2]
                    myfilter(text)
                else:
                    return text
            text = myfilter(text)
            xml = wechat.response_text(content=text)
            return xml

        if isinstance(wechat.message, ImageMessage):
            picurl = wechat.message.picurl                     # 对应于 XML 中的 PicUrl
            media_id = wechat.message.media_id                 # 对应于 XML 中的 MediaId

        if isinstance(wechat.message, VoiceMessage):
            media_id = wechat.message.media_id                 # 对应于 XML 中的 MediaId
            format = wechat.message.format                     # 对应于 XML 中的 Format
            recognition = wechat.message.recognition           # 对应于 XML 中的 Recognition

        if isinstance(wechat.message, VideoMessage) or isinstance(wechat.message, ShortVideoMessage):
            media_id = wechat.message.media_id                 # 对应于 XML 中的 MediaId
            thumb_media_id = wechat.message.thumb_media_id     # 对应于 XML 中的 ThumbMediaId

        if isinstance(wechat.message, LocationMessage):
            location = wechat.message.location                 # Tuple(X, Y)，对应于 XML 中的 (Location_X, Location_Y)
            scale = wechat.message.scale                       # 对应于 XML 中的 Scale
            label = wechat.message.label                       # 对应于 XML 中的 Label

        if isinstance(wechat.message, LinkMessage):
            title = wechat.message.title                       # 对应于 XML 中的 Title
            description = wechat.message.description           # 对应于 XML 中的 Description
            url = wechat.message.url                           # 对应于 XML 中的 Url

        if isinstance(wechat.message, EventMessage):
            if wechat.message.type == 'subscribe':  # 关注事件(包括普通关注事件和扫描二维码造成的关注事件)
                key = wechat.message.key                        # 对应于 XML 中的 EventKey (普通关注事件时此值为 None)
                ticket = wechat.message.ticket                  # 对应于 XML 中的 Ticket (普通关注事件时此值为 None)

                text = '''小Q等您很久了，快来调戏我吧！

功能包括：聊天、笑话、图片、天气、问答、百科、故事、新闻、菜谱、星座、凶吉、成语接龙、快递、飞机、列车、计算

你可以这样问他：
讲笑话
明天天气
查快递
看新闻
刘德华是谁
范冰冰照片
你是傻逼吗
...'''
                xml = wechat.response_text(content=text)
                return xml

            elif wechat.message.type == 'unsubscribe':  # 取消关注事件（无可用私有信息）
                pass
            elif wechat.message.type == 'scan':  # 用户已关注时的二维码扫描事件
                key = wechat.message.key                        # 对应于 XML 中的 EventKey
                ticket = wechat.message.ticket                  # 对应于 XML 中的 Ticket
            elif wechat.message.type == 'location':  # 上报地理位置事件
                latitude = wechat.message.latitude              # 对应于 XML 中的 Latitude
                longitude = wechat.message.longitude            # 对应于 XML 中的 Longitude
                precision = wechat.message.precision            # 对应于 XML 中的 Precision
            elif wechat.message.type == 'click':  # 自定义菜单点击事件
                key = wechat.message.key                        # 对应于 XML 中的 EventKey
            elif wechat.message.type == 'view':  # 自定义菜单跳转链接事件
                key = wechat.message.key                        # 对应于 XML 中的 EventKey
            elif wechat.message.type == 'templatesendjobfinish':  # 模板消息事件
                status = wechat.message.status                  # 对应于 XML 中的 Status
            elif wechat.message.type in ['scancode_push', 'scancode_waitmsg', 'pic_sysphoto',
                                         'pic_photo_or_album', 'pic_weixin', 'location_select']:  # 其他事件
                key = wechat.message.key                        # 对应于 XML 中的 EventKey


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    # set token or get from environments
    TOKEN = os.getenv('WECHAT_TOKEN', 'liaojuan520')
    AES_KEY = os.getenv('WECHAT_AES_KEY', '')
    APPID = os.getenv('WECHAT_APPID', '')

    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    encrypt_type = request.args.get('encrypt_type', 'raw')
    msg_signature = request.args.get('msg_signature', '')
    try:
        check_signature(TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        abort(403)
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        return echo_str

    # POST request
    if encrypt_type == 'raw':
        # plaintext mode
        msg = parse_message(request.data)
        if msg.type == 'text':
            if msg.content.startswith('#'):
                if msg.content[1:] == 'send':
                    rt = requests.get('http://api.wowapi.org/faduanxin/')
                    text = rt.text
                else:
                    text = 'input error'
            elif msg.content in ['help', u'帮助']:
                text = '''功能包括：聊天、笑话、图片、天气、问答、百科、故事、新闻、菜谱、星座、凶吉、成语接龙、快递、飞机、列车、计算

你可以这样问他：
明天天气
查快递
看新闻
刘德华是谁
范冰冰照片
你是傻逼吗
...
随意聊天，不要太拘谨哦！'''
            else:
                text = robot(msg.content, msg.source[:10]) #取消息来源前10位，因为不允许特殊符号
            reply = create_reply(text, msg)
        elif msg.type =='event':
            if msg.event == 'subscribe':
                text = '小Q等您很久了，快来调戏我吧！回复【帮助】获取使用指南！'
                reply = create_reply(text, msg)
        else:
            reply = create_reply('Sorry, can not handle this for now', msg)
        return reply.render()
    else:
        # encryption mode
        from wechatpy.crypto import WeChatCrypto

        crypto = WeChatCrypto(TOKEN, AES_KEY, APPID)
        try:
            msg = crypto.decrypt_message(
                request.data,
                msg_signature,
                timestamp,
                nonce
            )
        except (InvalidSignatureException, InvalidAppIdException):
            abort(403)
        else:
            msg = parse_message(msg)
            if msg.type == 'text':
                reply = create_reply(msg.content, msg)
            else:
                reply = create_reply('Sorry, can not handle this for now', msg)
            return crypto.encrypt_message(reply.render(), nonce, timestamp)


if __name__ == '__main__':
    app.run('127.0.0.1', 8001, debug=True)
