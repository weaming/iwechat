# coding: utf8
# 图灵机器人接口

import json
import requests as rq

token_key = 'e8151bef6a9f9deaf641a7c71b5cb0bc'

def robot(info=u'你好', userid='123', raw=False):
    rt = rq.get('http://www.tuling123.com/openapi/api?key=' + token_key + '&info=' + info + '&userid=' + userid)
    rt_text = rt.text.replace('<br>','\\n')
    tl = json.loads(rt_text)
    if raw: return tl

    # 判断消息类型
    if tl['code']==100000: #文字
        text = tl['text']
    elif tl['code']==200000: #链接
        text = tl['text']+'\n'+tl['url']
    elif tl['code']==302000: #新闻
        text = tl['text']+'\n\n'
        lenth = len(tl['list'])
        for index,i in enumerate(tl['list']):
            text = text + i['article'] + ' [' + i['source'] + ']\n' + i['detailurl']
            if index < lenth-1:
                text += '\n\n'
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
    return text
