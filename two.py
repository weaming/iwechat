# coding: utf-8

import sys
import time
from robot import turing, wbs_robot

last = None


def p(x):
    with open('chat.txt', 'a') as f:
        f.write((x+'\n').encode('utf-8'))
    print x.encode(sys.stdin.encoding, 'ignore')


def alice(msg):
    global last
    last = turing(msg, userid='Alice')
    out = 'Alice: %s' % last
    return out


def bob(msg):
    global last
    last = turing(msg, userid='Bob')
    out = 'Bob  : %s' % last
    return out

if __name__ == '__main__':
    last = unicode(raw_input('Input start sentence: '), sys.stdin.encoding)
    while True:
        out = alice(last)
        p(out)
        time.sleep(0.5)

        out = bob(last)
        p(out)
        time.sleep(0.5)




