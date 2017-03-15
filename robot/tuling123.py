# coding: utf8
# 图灵机器人接口

import json
import requests as rq

token_key = 'e8151bef6a9f9deaf641a7c71b5cb0bc'


def turing(info=u'你好', userid='123', raw=False, filter_func=None):
    rt = rq.get('http://www.tuling123.com/openapi/api?key=' + token_key + '&info=' + info + '&userid=' + userid)
    rt_text = rt.text.replace('<br>', r'\n')
    res = json.loads(rt_text)
    if raw:
        return res

    # 判断消息类型
    if res['code'] == 100000:  # 文字
        text = res['text']

    elif res['code'] == 200000:  # 链接
        text = res['text'] + '\n' + res['url']

    elif res['code'] == 302000:  # 新闻
        text = res['text'] + '\n\n'
        for index, i in enumerate(res['list']):
            text += '%s[%s]\n%s\n\n' % (i['article'], i['source'], i['detailurl'])

    elif res['code'] == 308000:  # 菜谱
        text = res['text'] + '\n\n'
        max_item = 5
        for index, i in enumerate(res['list']):
            if index < max_item:
                text += '%s:\n%s\n%s\n\n' % (i['name'], i['info'], i['detailurl'])

    elif res['code'] == 305000:  # 列车
        text = res['text'] + '\n\n'
        for index, i in enumerate(res['list']):
            text += '%s:\n%s-->%s\n%s--%s' % (i['trainnum'], i['start'], i['terminal'], i['starttime'], i['endtime'])
            if i['detailurl']:
                text += '\n' + i['detailurl']

    else:
        print(res)
        text = res['text']

    text = text.rstrip()
    if filter_func and callable(filter_func):
        text = filter_func(text)
    return text
