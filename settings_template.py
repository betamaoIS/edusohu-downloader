#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 18:39:34 2019

@author: WxJun
"""
import os

USER = 'your name'
PASSWD = 'your password'

HOST = 'https://edu.aqniu.com'
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

OUTDIR = 'G:\\gaga'
DATADIR = '.\\data'

FFMPEG = r'Z:\Tools\ffmpeg.exe'
FFMPEG_LOGLEVEL = 'warning'

OUTDIR = os.path.abspath(OUTDIR)
DATADIR = os.path.abspath(DATADIR)