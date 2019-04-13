#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  13 17:52:19 2019

@author: WxJun
"""
import threading

from m3u8_downloader import M3U8Downloader
import logging

logger = logging.getLogger('edusoho')


class M3u8ThreadDown(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self) -> None:
        while True:
            data = self.queue.get()
            playlist_url = data['playlist_url']
            tmp_dir = data['tmp_dir']
            out_dir = data['out_dir']
            filename = data['filename']
            logger.info('start download \t' + filename)
            downloader = M3U8Downloader(playlist_url)
            downloader.download(tmp_dir, out_dir, filename)
            self.queue.task_done()