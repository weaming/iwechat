# -*- coding: utf-8 -*-
import os
import requests

from flask import Flask, request, abort, render_template
from tuling123 import robot

from wechat_sdk import WechatConf
from wechat_sdk import WechatBasic

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import (
    InvalidSignatureException,
    InvalidAppIdException,
)

app = Flask(__name__)

# set token or get from environments
TOKEN = os.getenv('WECHAT_TOKEN', 'liaojuan520')
AES_KEY = os.getenv('WECHAT_AES_KEY', '')
APPID = os.getenv('WECHAT_APPID', '')


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

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
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
    app.run('127.0.0.1', 9003, debug=True)
