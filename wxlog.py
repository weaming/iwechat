# coding: utf-8

import sys
import functools
from pprint import pprint as pp
from util import *

"""
TEXT       = 'Text'
MAP        = 'Map'
CARD       = 'Card'
NOTE       = 'Note'
SHARING    = 'Sharing'
PICTURE    = 'Picture'
RECORDING  = 'Recording'
ATTACHMENT = 'Attachment'
VIDEO      = 'Video'
FRIENDS    = 'Friends'
SYSTEM     = 'System'
"""


def block(v='*', n=40):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(v * n)
            result = func(*args, **kwargs)
            print(v * n + '\n')
            return result

        return wrapper

    return decorator


@block(v='=')
def log(msg, rv=None):
    # pp(msg)
    msgs = []

    text = msg['Text']
    is_group = is_group_msg(msg)
    user_text = ''

    # User
    if is_group:
        user_text += u'Actual: %s [%s]' % (msg['ActualNickName'], msg['ActualUserName'])
        msgs.append(user_text)

    # From
    if is_group:
        # 群消息
        group_name = get_group_info(msg)
        uin = get_group_info(msg, info='uin')

        tmp = u'From: %s [%s]' % (group_name, uin)
    else:
        user_name = get_user_info(msg)
        remark_name = get_user_info(msg, info='remarkname')
        uin = get_user_info(msg, info='uin')
        tmp = u'From: %s [%s]' % (remark_name or user_name, uin)
    msgs.append(tmp)

    # TO
    msgs.append(u'To: %s' % get_self_name(msg))

    # detail
    msgs.append(u'[*] %s' % text)
    if rv:
        msgs.append(u'[+] %s' % rv)

    print('\n'.join(msgs).encode(sys.stdin.encoding, 'replace'))


def log_it(func):
    @functools.wraps(func)
    def wrapper(msg, **kwargs):
        result = func(msg, **kwargs)
        log(msg, result)
        return result

    return wrapper

