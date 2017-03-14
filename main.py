# coding: utf-8

import sys
import itchat
from itchat.content import TEXT, MAP, CARD, NOTE, SHARING, SYSTEM, FRIENDS
from tuling123 import robot
from util import log_it, pp

UIN = {}
MP, CHATROOM, MEMBER = [], [], []
ALL = []
switch = True


@itchat.msg_register(TEXT, isGroupChat=True, isFriendChat=True)
@log_it
def chat_bot(msg):
    rcv = msg['Text']
    if msg['isAt'] or msg['Type'] == FRIENDS:
        return robot(rcv, userid=msg['FromUserName'])


@itchat.msg_register(TEXT)
@log_it
def replay_me(msg):
    rcv = msg['Text']
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


itchat.auto_login(hotReload=True)
itchat.run()
