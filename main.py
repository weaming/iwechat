# coding: utf-8

import sys
import itchat
from itchat.content import TEXT, MAP, CARD, NOTE, SHARING, SYSTEM, FRIENDS
from tuling123 import robot
from util import log_it, pp, is_group_msg

MYSELF = None

UIN = {}
MP, CHATROOM, MEMBER = [], [], []
ALL = []
online = True


@itchat.msg_register(TEXT, isGroupChat=True, isFriendChat=True)
@log_it
def chat_bot(msg):
    """ 群聊，好友聊天 """
    global online
    rcv = msg['Text']
    if online:
        if is_group_msg(msg) and msg['isAt'] or msg['Type'] == FRIENDS:
            return robot(rcv, userid=msg['FromUserName'])


@itchat.msg_register(TEXT)
@log_it
def replay_me(msg):
    """ 自己给自己发送消息 """
    global online
    rcv = msg['Text']

    if is_admin(msg):
        if rcv in (u'关闭', u'下线', u'close', u'shutdown'):
            online = False
            return str(online)
        elif rcv in (u'开启', u'上线', u'online'):
            online = True
            return str(online)

    return robot(rcv, userid=msg['FromUserName'])


@itchat.msg_register(SYSTEM)
def get_uin(msg):
    if msg['SystemInfo'] != 'uins': return

    update_list()
    for username in msg['Text']:
        member = itchat.utils.search_dict_list(ALL, 'UserName', username)
        nickname = member.get('NickName', '')
        uin = member['Uin']
        # update global var
        UIN[username] = uin
        print(('%s: %s' % (nickname, uin)).encode(sys.stdin.encoding, 'replace'))


def update_list(ins=itchat.instanceList[0]):
    global ALL, MEMBER, CHATROOM, MP

    MEMBER, CHATROOM, MP = ins.memberList, ins.chatroomList, ins.mpList
    ALL = MEMBER + CHATROOM + MP
    print('** Uin Updated **')


def is_admin(msg):
    global MYSELF
    if MYSELF is None:
        MYSELF = itchat.search_friends()
    return msg['FromUserName'] == MYSELF['UserName']

itchat.auto_login(hotReload=True)
itchat.run()
