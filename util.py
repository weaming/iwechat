# coding: utf-8

import sys
import itchat
from pprint import pprint as pp

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
    from_user_name = msg['FromUserName']
    to_user_name = msg['ToUserName']

    is_group = is_group_msg(from_user_name)

    my_display_name = itchat.search_friends()['NickName']
    user_text = ''

    # User
    if is_group:
        user_text += u'Actual: %s [%s]' % (msg['ActualNickName'], msg['ActualUserName'])
        msgs.append(user_text)

    # From
    if is_group:
        # 群消息
        group, _ = get_group(userName=from_user_name)
        group_name = group['NickName']
        uin = group['Uin']
        my_display_name = group['self']['DisplayName'] or my_display_name

        tmp = u'From: %s [%s]' % (group_name, uin)
    else:
        user = itchat.search_friends(userName=from_user_name)
        user_name = user['NickName']
        remark_name = user['RemarkName']
        uin = user['Uin']
        tmp = u'From: %s [%s]' % (remark_name or user_name, uin)
    msgs.append(tmp)

    # TO
    msgs.append(u'To: %s [%s]' % (my_display_name, to_user_name))

    # detail
    msgs.append(u'[*] %s' % text)
    if rv:
        msgs.append(u'[+] %s' % rv)

    print('\n'.join(msgs).encode(sys.stdin.encoding, 'replace'))


def log_it(func):
    def wrapper(msg, **kwargs):
        result = func(msg, **kwargs)
        log(msg, result)
        return result

    return wrapper


def get_group(*args, **kwargs):
    group = itchat.search_chatrooms(*args, **kwargs)
    member_list = group['MemberList']
    del group['MemberList']
    return group, member_list


def is_group_msg(from_user_name):
    if type(from_user_name) is dict:
        from_user_name = from_user_name['FromUserName']
    return from_user_name.startswith('@@')


def is_friends_msg(from_user_name):
    if type(from_user_name) is dict:
        from_user_name = from_user_name['FromUserName']
    return from_user_name[0] == '@' and from_user_name[1] != '@'
