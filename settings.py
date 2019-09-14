#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 18:39:34 2019

@author: WxJun
"""
import os

user = 'admin'
passwd = 'admin'

USER = username
PASSWD = password

# HOST = 'https://edu.aqniu.com'
HOST = 'https://www.aqniukt.com'
HEADERS = {
    'Cache-Control': 'max-age=0',
    'Origin': 'https://edu.aqniu.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; WOW64)'
                   'AppleWebKit/537.36 (KHTML, like Gecko)'
                   ' Chrome/74.0.3724.8 Safari/537.36'),
    'Accept': ('text/html,application/xhtml+xml,application'
               '/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
               'application/signed-exchange;v=b3'),
    'Referer': 'https://edu.aqniu.com/login',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

OUTDIR = r'G:\神秘网校'
DATADIR = 'data'

FFMPEG = r'E:\Tools\cmdtool\ffmpeg.exe'
FFMPEG_LOGLEVEL = 'error'

MAXTHREADS = 20

OUTDIR = os.path.abspath(OUTDIR)
DATADIR = os.path.abspath(DATADIR)
