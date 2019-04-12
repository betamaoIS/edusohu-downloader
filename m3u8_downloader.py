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


class M3U8Downloader:
    url_query_pattern = re.compile(r'(http[s]{0,1}://.*?)\?.*', re.I)

    def __init__(self, uri, timeout=None, headers=None,
                 ffmpeg_path = None,
                 ffmpeg_loglevel=None, definition='shd'):
        self.headers = headers if headers else HEADERS
        self.definition = definition
        self.ffmpeg_path = ffmpeg_path if ffmpeg_path else FFMPEG
        self.ffmpeg_loglevel = ffmpeg_loglevel if ffmpeg_loglevel else FFMPEG_LOGLEVEL
        self.uri = uri
        self.m3u8 = m3u8.load(uri=uri, timeout=timeout, headers=self.headers)

    def decode_key(self, key):
        if len(key) == 20:
            start = int(key[0].lower(), 36) % 7
            algorithm = int(key[start:start+2], 36) % 3
            if algorithm == 2:
                c9 = ord(key[8])-ord('a') + (int(key[9])+1)*26-ord('a')
                c10 = ord(key[10])-ord('a') + (int(key[11])+1)*26-ord('a')
                c14 = ord(key[15])-ord('a') + (int(key[16])+1)*26-ord('a')
                c15 = ord(key[17])-ord('a') + (int(key[18])+2)*26-ord('a')
                dec_key = key[0:8] + chr(c9) + chr(c10) + key[12:15] + chr(c14) + chr(c15) + key[19]
            else:
                if algorithm == 1:
                    index = '0-1-2-3-4-5-6-7-18-16-15-13-12-11-10-8'
                else:
                    index = '0-1-2-3-4-5-6-7-8-10-11-12-14-15-16-18'
                tmp_key = []
                for i in index.split('-'):
                    tmp_key.append(key[int(i)])
                dec_key = ''.join(tmp_key)
        elif len(key) == 17:
            index = '8-9-2-3-4-5-6-7-0-1-10-11-12-13-14-15'
            key = key[1:]
            tmp_key = []
            for i in index.split('-'):
                tmp_key.append(key[int(i)])
            dec_key = ''.join(tmp_key)
        else:
            logger.warning('the key maybe fakeToken!')
            dec_key = key
        logger.info('%s ==dec==> %s' %(key, dec_key))
        return dec_key

    def download(self, tmp_dir, out_dir, filename):
        if self.m3u8.is_variant:
            for index, playlist in enumerate(self.m3u8.playlists):
                if ('/%s/' % self.definition) in playlist.uri:
                    fetch_index = index
                    break
            try:
                downloader = M3U8Downloader(
                    self.m3u8.playlists[fetch_index].absolute_uri
                )
            except (ValueError, IndexError):
                logger.error('Invalid index When set definition!')
                return False
            downloader.download(tmp_dir, out_dir, filename)
                
        else:
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)
            key_urls = []
            m3u8_str = self.m3u8.dumps()
            for segment in self.m3u8.segments:
                key_url = segment.key.absolute_uri
                if key_url not in key_urls:  # 根据edusoho特性优化
                    key_value = self.decode_key(requests.get(key_url).text)  # 小坏小坏的，默认token只能使用一次，否则会返回一个虚假的16位token
                    key_urls.append(key_url)
                    m3u8_str = m3u8_str.replace(key_url, md5(key_url.encode("utf-8")))
                    str2file(key_value, tmp_dir + '\\' + md5(key_url.encode("utf-8")))
            m3u8_str = self.url_query_pattern.sub(r'\1', m3u8_str)
            m3u8_path = '%s\\%s.m3u8' % (tmp_dir, filename)
            str2file(m3u8_str, m3u8_path)
            mp4_path = '%s\\%s.mp4' % (out_dir, filename)
            ffmpeg_cmd = ffmpy.FFmpeg(
                    self.ffmpeg_path,
                    '-y -loglevel {}'.format(self.ffmpeg_loglevel),
                    inputs = {m3u8_path: '-allowed_extensions ALL -protocol_whitelist "file,http,crypto,tcp,https,tls"'},
                    outputs = {mp4_path: '-c copy'}
                    )
            # s = ffmpeg_cmd.cmd
            logger.info(ffmpeg_cmd.cmd)
            os.chdir(tmp_dir)
            # os.system(s)
            try:
                ffmpeg_cmd.run()
                str2file('', tmp_dir + '\\%s.has_down'%filename)


                return True
            except ffmpy.FFRuntimeError as e:
                logger.error(e)
                return False

def main():
    downloader = M3U8Downloader(uri=r'Kali Linux安全测试介绍.m3u8')
    # downloader.download(output='')
    downloader.decode_key('02nbaOVHi5n6f6cp4z4p') #02nbaOVHCbf6c0Tp

if __name__ == '__main__':
    # main()
    pass