# coding: utf-8

import sys
import os
import time
import shutil
import re
from datetime import datetime as dt
from pprint import pprint as pp

import itchat
from itchat.content import TEXT, SYSTEM, FRIENDS
from itchat.content import NOTE, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO
from itchat.utils import search_dict_list
from wxlog import log_it
from robot.tuling123 import turing
from util import *


def robot(query, *args, **kwargs):
    return turing(query, **kwargs)


online = True

UIN = {}
MYSELF = None
MP, CHATROOM, MEMBER, ALL = [], [], [], []

# {msg_id:(msg_from,msg_to,msg_time,msg_now_str,msg_type,msg_content,msg_url)}
msg_dict = {}


@log_it
def chat_bot(msg):
    """ 群聊，好友聊天 """
    if msg['Type'] != TEXT: return

    global online
    rcv = msg['Text']
    if online:
        if is_group_msg(msg) and not is_from_myself(msg):
            if msg['isAt'] or u'逗比群' in get_group_info(msg):
                return robot(rcv, userid=msg['FromUserName']+msg['ActualUserName'])
        elif msg['Type'] == FRIENDS:
            return robot(rcv, userid=msg['FromUserName'])


@log_it
def replay_me(msg):
    """ 自己给自己发送消息 """
    if msg['Type'] != TEXT: return

    global online
    rcv = msg['Text']

    if is_from_myself(msg) and msg['FromUserName'] == msg['ToUserName']:
        if online and rcv in (u'关闭', u'下线', u'close', u'shutdown'):
            online = False
            return str(online)
        elif not online and rcv in (u'开启', u'上线', u'online'):
            online = True
            return str(online)

        return robot(rcv, userid=msg['FromUserName'])


@itchat.msg_register(SYSTEM)
def update_uin(msg):
    if msg['SystemInfo'] != 'uins': return

    update_list()
    for username in msg['Text']:
        member = search_dict_list(ALL, 'UserName', username)
        nickname = member.get('NickName', '')
        uin = member['Uin']
        # update global var
        UIN[username] = uin
        print(('%s: %s' % (nickname, uin)).encode(sys.stdin.encoding, 'replace'))

    print('** Uin Updated **')


def clear_timeout_msg():
    """
    ClearTimeOutMsg用于清理消息字典，把超时消息清理掉
    为减少资源占用，此函数只在有新消息动态时调用
    """
    if len(msg_dict) > 0:
        for msgid in list(msg_dict):  # 由于字典在遍历过程中不能删除元素，故使用此方法
            if time.time() - msg_dict.get(msgid, None)["msg_time"] > 130.0:  # 超时两分钟
                item = msg_dict.pop(msgid)
                # print("超时的消息：", item['msg_content'])
                # 可下载类消息，并删除相关文件
                if item['msg_type'] == "Picture" \
                        or item['msg_type'] == "Recording" \
                        or item['msg_type'] == "Video" \
                        or item['msg_type'] == "Attachment":
                    print("要删除的文件：", item['msg_content'])
                    os.remove(item['msg_content'])


def save_history(msg):
    """
    将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
    没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
    """
    now = dt.now()
    # 获取用于展示给用户看的时间 2017/03/03 13:23:53
    msg_time_str = now.strftime('%Y-%m-%d %X')

    msg_id = msg['MsgId']  # 消息ID
    msg_time = msg['CreateTime']  # 消息时间

    user_name, group_name = get_from_info(msg)  # 消息发送人昵称
    msg_from = group_name + ' - ' + user_name if group_name else user_name

    msg_type = msg['Type']  # 消息类型
    msg_content = None  # 根据消息类型不同，消息内容不同
    msg_url = None  # 分享类消息有url

    # 图片 语音 附件 视频，可下载消息将内容下载暂存到当前目录
    if msg_type == 'Text':
        msg_content = msg['Text']
    elif msg_type == 'Picture':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg_type == 'Card':
        msg_content = msg['RecommendInfo']['NickName'] + r" 的名片"
    elif msg_type == 'Map':
        x, y, location = re.search(
            "<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = r"纬度->" + x.__str__() + " 经度->" + y.__str__()
        else:
            msg_content = r"" + location
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_url = msg['Url']
    elif msg['Type'] == 'Recording':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Attachment':
        msg_content = r"" + msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Video':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Friends':
        msg_content = msg['Text']

    # 更新字典
    # {msg_id:(msg_from,msg_time,msg_time_str,msg_type,msg_content,msg_url)}
    msg_dict[msg_id] = {
        "msg_from": msg_from, "msg_time": msg_time,
        "msg_time_str": msg_time_str, "msg_type": msg_type,
        "msg_content": msg_content, "msg_url": msg_url
    }
    # 清理字典
    clear_timeout_msg()


@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isGroupChat=True, isFriendChat=True)
def handle_msg(msg):
    save_history(msg)
    return replay_me(msg) or chat_bot(msg)


@itchat.msg_register(NOTE, isGroupChat=True, isFriendChat=True)
def when_revoke(msg):
    """
    收到note类消息，判断是不是撤回并进行相应操作
    """
    # 创建可下载消息内容的存放文件夹，并将暂存在当前目录的文件移动到该文件中
    save_dir = os.path.expanduser('~/Revocation')
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    msg['Content'] = _content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')
    # pp(msg)
    if '<revokemsg>' in _content:
        old_msg_id = re.search(r"<msgid>(.*?)</msgid>", _content).group(1)
        old_msg = msg_dict.get(old_msg_id, {})
        # print(old_msg_id, old_msg)
        msg_send = u"您的好友：{msg_from} 在 [{msg_time_str}]，撤回了一条 [{msg_type}] 消息，内容如下：{msg_content}" \
            .format(msg_from=old_msg.get('msg_from', None), msg_time_str=old_msg.get('msg_time_str'),
                    msg_type=old_msg['msg_type'], msg_content=old_msg.get('msg_content'))

        old_msg_type = old_msg['msg_type']
        if old_msg_type == SHARING and old_msg.get('msg_url', None):
            msg_send += u", 链接: " + old_msg['msg_url']
        elif old_msg_type in (PICTURE, VIDEO, ATTACHMENT):
            msg_send += u", 存储在%s文件夹中" % save_dir
            _content = old_msg['msg_content']
            shutil.move(_content, save_dir)

            if old_msg_type == PICTURE:
                itchat.send_image(os.path.join(save_dir, _content), toUserName='filehelper')
            else:
                itchat.send_file(os.path.join(save_dir, _content), toUserName='filehelper')

        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手

        msg_dict.pop(old_msg_id)
        clear_timeout_msg()


def update_list(ins=itchat.instanceList[0]):
    global ALL, MEMBER, CHATROOM, MP

    MEMBER, CHATROOM, MP = ins.memberList, ins.chatroomList, ins.mpList
    ALL = MEMBER + CHATROOM + MP
    print('** List Updated **')


def is_from_myself(msg):
    global MYSELF
    if MYSELF is None:
        MYSELF = itchat.search_friends()

    return msg['FromUserName'] == MYSELF['UserName']


if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    itchat.run()
