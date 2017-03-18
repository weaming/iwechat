# coding: utf-8

import itchat


def is_group_msg(msg):
    from_user_name = msg['FromUserName']
    return from_user_name.startswith('@@')

def is_friends_msg(msg):
    from_user_name = msg['FromUserName']
    return from_user_name[0] == '@' and from_user_name[1] != '@'

def get_group(*args, **kwargs):
    """
    调用方法同 itchat.search_chatrooms()
    拆分群属性信息和群成员列表
    """
    group = itchat.search_chatrooms(*args, **kwargs)
    member_list = group['MemberList']
    del group['MemberList']
    return group, member_list

def get_group_by_msg(msg, info='group'):
    if is_group_msg(msg):
        group, member_list = get_group(userName=msg['FromUserName'])
        if info == 'group':
            return group
        if info == 'members':
            return member_list
        raise Exception('Info type error')
    return None


def get_group_info(msg, info='nickname'):
    info = info.lower()
    if is_group_msg(msg):
        group = get_group_by_msg(msg)
        if info == 'nickname':
            return group['NickName']
        if info == 'uin':
            return group['Uin']
        raise Exception('Info type error')
    return None

def get_from_info(msg):
    if is_group_msg(msg):
        return msg['ActualNickName'], get_group_info(msg)
    else:
        return get_user_info(msg), None


def get_user_info(msg, info='nickname'):
    info = info.lower()
    if is_friends_msg(msg):
        user = itchat.search_friends(userName=msg['FromUserName'])
        if info == 'nickname':
            return user['NickName']
        if info == 'remarkname':
            return user['RemarkName']
        if info == 'uin':
            return user['Uin']
        raise Exception('Info type error')
    return None

def get_self_name(msg):
    my_nick_name = itchat.search_friends()['NickName']
    if is_group_msg(msg):
        group = get_group_by_msg(msg)
        return group['self']['DisplayName'] or my_nick_name
    return my_nick_name

