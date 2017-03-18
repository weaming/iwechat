# coding: utf-8

import sys
import os
import time
import shutil
import re

import itchat
from wxlog import log_it, is_group_msg
from itchat.content import TEXT, SYSTEM, FRIENDS
from itchat.content import NOTE, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO
from robot.tuling123 import turing
from robot.wbscms import wbs_robot
from pprint import pprint as pp


def robot(query, *args, **kwargs):
    return turing(query, **kwargs)

online = True

UIN = {}
MYSELF = None
MP, CHATROOM, MEMBER, ALL = [], [], [], []

# {msg_id:(msg_from,msg_to,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
msg_dict = {}


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

    if is_admin(msg) and msg['FromUserName'] == msg['ToUserName']:
        if rcv in (u'关闭', u'下线', u'close', u'shutdown'):
            online = False
            return str(online)
        elif rcv in (u'开启', u'上线', u'online'):
            online = True
            return str(online)

        return robot(rcv, userid=msg['FromUserName'])


@itchat.msg_register(SYSTEM)
def update_uin(msg):
    if msg['SystemInfo'] != 'uins': return

    update_list()
    for username in msg['Text']:
        member = itchat.utils.search_dict_list(ALL, 'UserName', username)
        nickname = member.get('NickName', '')
        uin = member['Uin']
        # update global var
        UIN[username] = uin
        print(('%s: %s' % (nickname, uin)).encode(sys.stdin.encoding, 'replace'))

    print('** Uin Updated **')


#ClearTimeOutMsg用于清理消息字典，把超时消息清理掉
#为减少资源占用，此函数只在有新消息动态时调用
def ClearTimeOutMsg():
    if len(msg_dict) > 0:
        for msgid in list(msg_dict): #由于字典在遍历过程中不能删除元素，故使用此方法
            if time.time() - msg_dict.get(msgid, None)["msg_time"] > 130.0: #超时两分钟
                item = msg_dict.pop(msgid)
                #print("超时的消息：", item['msg_content'])
                #可下载类消息，并删除相关文件
                if item['msg_type'] == "Picture" \
                        or item['msg_type'] == "Recording" \
                        or item['msg_type'] == "Video" \
                        or item['msg_type'] == "Attachment":
                    print("要删除的文件：", item['msg_content'])
                    os.remove(item['msg_content'])

#将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
#没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS])
def Revocation(msg):
    mytime = time.localtime()  # 这儿获取的是本地时间
    #获取用于展示给用户看的时间 2017/03/03 13:23:53
    msg_time_touser = mytime.tm_year.__str__() \
        + "/" + mytime.tm_mon.__str__() \
        + "/" + mytime.tm_mday.__str__() \
        + " " + mytime.tm_hour.__str__() \
        + ":" + mytime.tm_min.__str__() \
        + ":" + mytime.tm_sec.__str__()

    msg_id = msg['MsgId'] #消息ID
    msg_time = msg['CreateTime'] #消息时间
    msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName'] #消息发送人昵称
    msg_type = msg['Type'] #消息类型
    msg_content = None #根据消息类型不同，消息内容不同
    msg_url = None #分享类消息有url
    #图片 语音 附件 视频，可下载消息将内容下载暂存到当前目录
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

    #更新字典
    # {msg_id:(msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({
        msg_id: {"msg_from": msg_from, "msg_time": msg_time,
                 "msg_time_touser": msg_time_touser, "msg_type": msg_type,
                 "msg_content": msg_content, "msg_url": msg_url}
    })
    #清理字典
    ClearTimeOutMsg()

#收到note类消息，判断是不是撤回并进行相应操作
@itchat.msg_register(NOTE)
def SaveMsg(msg):
    # print(msg)
    #创建可下载消息内容的存放文件夹，并将暂存在当前目录的文件移动到该文件中
    save_dir = os.path.expanduser('~/Revocation')
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    if '<revokemsg>' in msg['Content']:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
        old_msg = msg_dict.get(old_msg_id, {})
        #print(old_msg_id, old_msg)
        msg_send = u"您的好友：{msg_from} 在 [{time_touser}]，撤回了一条 [{msg_type}] 消息，内容如下：{msg_content}".format(
            msg_from=old_msg.get('msg_from', None),
            time_touser=old_msg.get('msg_time_touser', None),
            msg_type=old_msg['msg_type'],
            msg_content=old_msg.get('msg_content', None),
        )

        old_msg_type = old_msg['msg_type']
        if old_msg_type == SHARING:
            msg_send += u", 链接: " + old_msg.get('msg_url', None)
        elif old_msg_type in (PICTURE, VIDEO, ATTACHMENT):
            msg_send += u", 存储在%s文件夹中" % save_dir
            _content = old_msg['msg_content']
            shutil.move(_content, save_dir)

            if old_msg_type == PICTURE:
                itchat.send_image(os.path.join(save_dir, _content), toUserName='filehelper')
            else:
                itchat.send_file(os.path.join(save_dir, _content), toUserName='filehelper')

        itchat.send(msg_send, toUserName='filehelper') #将撤回消息的通知以及细节发送到文件助手

        msg_dict.pop(old_msg_id)
        ClearTimeOutMsg()


def update_list(ins=itchat.instanceList[0]):
    global ALL, MEMBER, CHATROOM, MP

    MEMBER, CHATROOM, MP = ins.memberList, ins.chatroomList, ins.mpList
    ALL = MEMBER + CHATROOM + MP
    print('** List Updated **')


def is_admin(msg):
    global MYSELF
    if MYSELF is None:
        MYSELF = itchat.search_friends()

    return msg['FromUserName'] == MYSELF['UserName']


def run(hot_reload=True, use_thread=False):
    itchat.auto_login(hotReload=hot_reload)
    if use_thread:
        import thread
        thread.start_new_thread(itchat.run, ())
    else:
        itchat.run()

if __name__ == '__main__':
    run()
