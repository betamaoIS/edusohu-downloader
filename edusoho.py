#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 17:52:19 2019

@author: WxJun
"""

import requests
import re
import json
import os
import pickle
import logging

from lxml import etree
from m3u8_downloader import M3U8Downloader
from utils import str2file, readfile, escape
from settings import USER, PASSWD, HEADERS, HOST, OUTDIR, DATADIR


class Edusoho(object):
    session = None

    def __init__(self, user, passwd, host=None):
        host = host if host else HOST
        self.host = host.rstrip('/')
        self.user_data_dir = '%s\\%s\\%s' % (DATADIR, 
                                             escape(host.split('//')[1]), 
                                             escape(user))
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.cache_path = self.user_data_dir + '\\sessin.cache'
        self.login_url = self.host + '/login?goto=/'
        self.login_check_url = self.host + '/login_check'
        self._init_logger()
        if not self.is_login():
            if self.login(user, passwd):
                self.logger.info('login success')
                return
            else:
                self.logger.error('login failed')
                raise Exception('login failed')
        else:
            self.logger.info('login success')

    def is_login(self):
        url = self.host + '/settings'
        if self.session:
            resp = self.session.get(url=url)
            if resp.status_code != 302:
                return True

        cache = readfile(self.cache_path)
        if cache:
            self.session = pickle.loads(cache)
            resp = self.session.get(url=url)
            if resp.status_code != 302:
                return True
        return False

    def log_out(self):
        self.session = None
        str2file('', self.cache_path)
        self.logger.info('log out!')

    def has_downloaded(self):
        pass
        
    def login(self, user, passwd):
        self.session = requests.Session()
        self.session.headers = HEADERS
        resp = self.session.get(url=self.login_url)
        csrf_token = re.findall(r'content="(.*?)" name="csrf-token"',
                                resp.text)
        data = {
                '_username': user,
                '_password': passwd,
                '_remember_me': 'on',
                '_target_path': '/mobile/',
                '_csrf_token': csrf_token
        }
        resp = self.session.post(url=self.login_check_url,
                                 data=data, allow_redirects=False)
        if 'mobile' in resp.text:
            cache = pickle.dumps(self.session)
            return str2file(cache, self.cache_path)

        else:
            return False

    def _get_chapter_list(self, course_id):
        course_url = self.host + '/my/course/' + str(course_id)
        resp = self.session.get(url=course_url)
        selector = etree.HTML(resp.text)
        data = selector.xpath('/html/body/div[1]/div[3]/div/div[1]'
                              '/section/div[2]/div[5]/text()')
        return json.loads(''.join(data))

    def download_course(self, course_id, out_dir, tmp_dir=None):
        tmp_dir = tmp_dir if tmp_dir else self.user_data_dir
        lessons = self._get_chapter_list(course_id)
        chapter_id = 0
        chapter_name = ''
        for lesson in lessons:
            res_type = lesson['type']
            status = lesson['status']
            if (status == 'published' and (res_type == 'video' 
                    or res_type == 'download')):
                title = lesson['title']
                task_id = lesson['taskId']
                url = ('%s/course/%s/task/%s/activity_show' # ?blanck=1
                       % (self.host, course_id, task_id))
                new_out_dir = '%s\\第%s章-%s' % (out_dir, chapter_id, escape(chapter_name))
                new_tmp_dir = '%s\\第%s章-%s' % (tmp_dir, chapter_id, escape(chapter_name))
                file_name = escape(title)
                if res_type == 'video':
                    self._download_video(url, file_name, new_out_dir, new_tmp_dir)
                else:
                    self._download_doc(url, file_name, new_out_dir, new_tmp_dir)
            elif res_type == 'chapter':
                chapter_id = lesson['number']
                chapter_name = lesson['title']
    
    def _download_doc(self, url, file_name, dir_name, tmp_dir):
        if os.path.exists('%s\\%s.has_down'%(tmp_dir, file_name)):
            return
        resp = self.session.get(url)
        if '不能访问教学计划'.encode('utf8') in resp.text.encode('utf8'):
            self.logger.error('无权限访问该课程！')
            return
        doc_path = ''.join(re.findall('data-url="(.*?)"', resp.text))
        doc_url = self.host + doc_path
        resp = self.session.get(doc_url)
        # TODO: 下载的文件名在查询参数里，可通过头获得attname，再写准确的
        str2file(resp.content, dir_name + '\\' + file_name + '.pdf')
        str2file('', dir_name + '\\%s.has_down' % file_name)
    def _download_video(self, url, title, out_dir, tmp_dir, clarity='shd'):
        if os.path.exists(tmp_dir + '\\%s.has_down'%title):
            return
        url = re.sub(r'/show\?', r'/activity_show\?', url)
        resp = self.session.get(url=url)
        if '不能访问教学计划' in resp.text:
            self.logger.error('无权限访问该课程！')
            return
        playlist_url = ''.join(re.findall('data-url="(.*?)"', resp.text))
        self.logger.info('start download' + title)
        downloader = M3U8Downloader(playlist_url)
        downloader.download(tmp_dir, out_dir, title)

    def _init_logger(self, log_path=None, level=logging.DEBUG):
        self.logger = logging.getLogger('edusoho')
        self.logger.setLevel(level)
        # 创建一个handler，用于写入日志文件
        self.log_path = log_path if log_path else (self.user_data_dir + '\\test.log')

        fh = logging.FileHandler(self.log_path, 'a')
        fh.setLevel(level)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # 定义handler的输出格式
        formatter = logging.Formatter(
                '[%(asctime)s] %(filename)s->%(funcName)s line:%(lineno)d [%(levelname)s]%(message)s'
                )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        # self.logger.

    
def main():
    mySpider = Edusoho(USER, PASSWD)
    mySpider.download_course(course_id=83, out_dir=OUTDIR)


if __name__ == '__main__':
    main()
