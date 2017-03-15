# coding: utf8

import requests as http


def wbs_robot(msg):
    api = 'http://api.wbscms.com/api.php?msg='
    try:
        res = http.get(api+msg)
        js = res.json()
        if res.status_code == 200:
            return js['wbscmsapi']
        else:
            print(js)
    except Exception as e:
        print e
        return 'error on http'
