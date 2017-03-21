# coding: utf-8
# http://www.chatbot.cn/
import requests

def get_api(app_key='58d13e7a0e00006621a01b36'):
    return 'http://api.smartnlp.cn/cloud/robot/%s/answer?q=' % app_key

def ask(question):
    try:
        js = requests.get(get_api()+question).json()
        return js['answers'][0]['respond']
    except Exception as e:
        print(e)
        return u'机器人也无能为力'

if __name__ == '__main__':
    print ask('nihao')
