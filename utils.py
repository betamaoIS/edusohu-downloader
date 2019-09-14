#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 20:20:19 2019

@author: WxJun
"""

import io
import hashlib
import logging
import re

logger = logging.getLogger('edusoho')


def escape(s):
#    s = s if isinstance(s, bytes) else s.encode('utf8')
#    return re.sub('[\\/*?"<>|:]'.encode('utf8'),'-'.encode('utf8'), s)
    return re.sub(r'[\\/*?"<>|:]','-', s)


def str2file(s, path, m='wb'):
    s = s if isinstance(s, bytes) else s.encode('utf8')
    try:
        with io.open(path, m) as f:
            f.write(s)
        return True
    except Exception as e:
        logger.error(e)
        return False


def readfile(path):
    try:
        with io.open(path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(e)
        return ''


def md5(s):
    if isinstance(s, str):
        s = s.encode('utf8')
    return hashlib.md5(s).hexdigest()
