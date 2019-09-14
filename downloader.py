#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import os

import m3u8
import requests
import re
import ffmpy
import logging

from utils import str2file, md5
from settings import HEADERS, FFMPEG, FFMPEG_LOGLEVEL

logger = logging.getLogger('edusoho')


def main():
    ...


def download(ffmpeg_path, ffmpeg_loglevel, m3u8_path, mp4_path):
    ffmpeg_cmd = ffmpy.FFmpeg(
        ffmpeg_path,
        '-y -loglevel {}'.format(ffmpeg_loglevel),
        inputs={m3u8_path: '-allowed_extensions ALL -protocol_whitelist "file,http,crypto,tcp,https,tls"'},
        outputs={mp4_path: '-c copy'}
    )
    logger.info(ffmpeg_cmd.cmd)
    try:
        ffmpeg_cmd.run()
    except ffmpy.FFRuntimeError as e:
        logger.error(e)
        res = False
    else:
        res = True
    return res

if __name__ == '__main__':
    download()