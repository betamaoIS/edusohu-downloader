#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 17:52:19 2019

@author: WxJun
"""

import json
import logging
import os
import pickle
import re
from queue import Queue
from urllib.parse import parse_qs
from urllib.parse import urljoin, urlparse

import requests
from lxml import etree

from downloader import M3u8ThreadDown
from settings import USER, PASSWD, HEADERS, OUTDIR, DATADIR, MAXTHREADS
from datastorage import SqliteSession, Course, CourseDetail, User
from utils import str2file, escape, md5
from pprint import pprint
import m3u8

TRIM_KEY_URI = re.compile(r'https://www.aqniukt.com/hls/(\d+/clef/\w{32})')
TRIM_FULL_KEY_URI = re.compile(r'(#EXT-X-KEY:METHOD=AES-128,URI=")https://www.aqniukt.com/hls/(\d+/clef/\w{32})')
TRIM_USER_INFO = re.compile(r'(.*)\?.*')

class Edusoho(object):
    session = None
    course_name = 'null'
    course_details = {}  # {course_id:{'course_name':,'course_url':,'course_data':[] }}
    HTTP_OK = 200
    COURSE_NAME = 0
    COURSE_DATA = 1

    def _init_url(self):
        self.cache_path = os.path.join(self.user_data_dir, 'session.cache')
        self.login_url = urljoin(self.host, 'login?goto=/')  # 登陆成功后访问主页
        self.login_check_url = urljoin(self.host, 'login_check')  # 成功访问则登陆成功

    def _init_dir(self):
        url_object = urlparse(self.host)
        self.user_data_dir = r'%s\%s\%s' % (DATADIR,
                                            escape(url_object.netloc),
                                            escape(self.user))
        os.makedirs(self.user_data_dir, exist_ok=True)

    def _init_queue(self):
        self.video_queue = Queue()
        for i in range(MAXTHREADS):
            t = M3u8ThreadDown(self.video_queue)
            t.setDaemon(True)
            t.start()

    def __init__(self, user=None, passwd=None, host='https://www.aqniukt.com'):
        self.user = user
        self.host = host
        self._init_dir()
        self._init_url()
        self._init_logger()
        self._init_queue()
        # 检查登陆
        if not self.is_login():
            if not self.login(user, passwd):
                raise Exception('login failed')
        self.sql_session_instance = SqliteSession()
        self.sql_session = self.sql_session_instance.session
        self.crawl_my_course()

    def is_login(self):
        url = urljoin(self.host, 'settings')  # 该页面需要登陆后才能访问
        if self.session:
            resp = self.session.get(url=url)
            if resp.status_code != 302:
                self.logger.info('is log in!')
                return True
        else:
            try:
                self.session = pickle.load(open(self.cache_path, 'rb'))
                resp = self.session.get(url=url)
            except Exception as e:
                self.logger.error(str(e))
            else:
                if resp.status_code != 302:
                    self.logger.info('is log in!')
                    return True
        self.logger.info('is NOT log in!')
        return False

    def log_out(self):
        self.session = None
        str2file('', self.cache_path)
        self.logger.info('log out!')

    def has_downloaded(self):
        pass

    def login(self, user, passwd):
        """登陆系统

        :param user:
        :param passwd:
        :return:
        """
        if not user or not passwd:
            self.logger.error('为输入用户名或密码，无法登陆！')
            return False
        self.session = requests.Session()
        self.session.headers = HEADERS
        resp = self.session.get(url=self.login_url)
        csrf_token = re.findall(r'content="(.*?)" name="csrf-token"', resp.text)
        data = {
            '_username': user,
            '_password': passwd,
            '_remember_me': 'on',
            '_target_path': '/mobile/',
            '_csrf_token': csrf_token
        }
        resp = self.session.post(url=self.login_check_url, data=data, allow_redirects=False)
        if 'mobile' in resp.text:  # 登陆成功会跳转到登陆时指定的链接
            try:
                self.logger.info('登录成功！')
                pickle.dump(self.session, open(self.cache_path, 'wb'))
            except Exception as e:
                self.logger.error('将登录令牌存储于文件时失败：' + str(e))
            return True
        else:
            self.logger.info('登录失败！')
            return False

    def _make_chapter_list(self, course_id, force=False):
        """对于指定的课程号，解析其课程章节数据。

        :param course_id: 指定课程号
        :param force: 是否强制解析，当指定的课程号不在”我的课程“列表里时，可进行强制解析
        :return:
        """
        if course_id not in self.course_details:
            self.logger.info('指定的课程号不在已购课程列表里。。。')
            if force:
                course_url = urljoin(self.host, '/my/course/' + str(course_id))
            else:
                return None
        else:
            course_url = self.course_details[course_id]['course_url']
        try:
            resp = self.session.get(url=course_url)
        except Exception as e:
            self.logger.error('请求出错：' + str(e))
            return None
        else:
            selector = etree.HTML(resp.text)
            course_detail_data = selector.xpath('//*[@class="hidden js-hidden-cached-data"]/text()')[(-1)]
            # course_name = selector.xpath('//*[@class="course-detail-heading"]/text()')[(-1)]
            self.course_details[course_id]['course_data'] = json.loads(course_detail_data)
            return True

    def resolve_my_course(self):
        for course_id in self.course_details:
            self.logger.info('start resolve %s ..' % self.course_details[course_id]['course_name'])
            self.download_course(course_id)

    def download_course(self, course_id):
        self.logger.info('start download %s ....' % self.course_details[course_id]['course_name'])
        res = self._make_chapter_list(course_id)
        if not res:
            return
        chapter_id = 0
        chapter_name = '无名章'
        for lesson in self.course_details[course_id]['course_data']:
            if lesson['type'] == 'chapter':
                chapter_id = lesson['number']
                chapter_name = lesson['title']
            elif lesson['status'] == 'published':
                title = lesson['title']
                section_id = lesson['number']
                if lesson['type'] == 'video':  # 为视频
                    section_md5 = md5(str(course_id) + chapter_name + str(section_id) + title)
                    # 首先判断该数据是否已存在于数据库，是则跳过
                    if self.sql_session.query(Course.section_md5).filter(Course.section_md5 == section_md5).count() > 0:
                        self.logger.debug('当前课程信息已存在')
                        continue
                    # 获取播放链接信息
                    self.logger.debug('start log %s...' % title)
                    url = urljoin(self.host, 'course/%s/task/%s/activity_show' % (course_id, lesson['taskId']))
                    resp = self.session.get(url=url)
                    if '不能访问教学计划' in resp.text:
                        self.logger.error('无权限访问该课程！')
                        return
                    playlist_url = re.search('data-url="(.*?)"', resp.text).group(1)
                    # 获取播放列表
                    resp = self.session.get(playlist_url)
                    if resp.status_code != self.HTTP_OK:
                        continue
                    playlist_text = resp.text
                    # 解析播放列表：对每一种清晰度，获取对应的m3u8文件与相应的aeskey
                    m3u8_obj = m3u8.loads(playlist_text)
                    for playlist in m3u8_obj.playlists:
                        uri = playlist.absolute_uri
                        bandwidth = playlist.stream_info.bandwidth
                        # 解析对应清晰度的m3u8
                        resp = self.session.get(uri)
                        m3u8_full = resp.text
                        # 只存储必要的数据
                        m3u8_text = filter_header(m3u8_full)
                        
                        m3u8_obj = m3u8.loads(m3u8_full)
                        # 下载密钥
                        keys = {}
                        for key in m3u8_obj.keys:
                            u = TRIM_KEY_URI.sub(r'\1',key.absolute_uri)
                            if u not in keys:
                                resp = self.session.get(key.absolute_uri)
                                keys[u] = decode_key(resp.text)

                        # 存储数据信息
                        course_detail = CourseDetail(section_md5=section_md5, type='video', width=bandwidth,
                                                     m3u8=m3u8_text, m3u8_full=None, aes_key=json.dumps(keys),
                                                     has_download=False)
                        self.sql_session.add(course_detail)
                    # 添加课程节信息
                    course = Course(course_id=course_id, course_name=self.course_details[course_id]['course_name'],
                                    chapter_id=chapter_id, chapter_name=chapter_name, section_id=section_id,
                                    section_name=title, section_md5=section_md5)
                    self.sql_session.add(course)
                    try:
                        self.sql_session.commit()
                    except Exception as e:
                        self.logger.error('提交数据失败：' + str(e))
                        self.sql_session.rollback()
                elif lesson['type'] == 'download':
                    # 检查是否已存在
                    section_md5 = md5(str(course_id) + str(chapter_name) + str(section_id) + str(title))
                    if self.sql_session.query(Course.section_md5).filter(Course.section_md5 == section_md5).count() > 0:
                        self.logger.debug('当前课程信息已存在')
                        continue
                    """ 暂时不处理该类文件
                    # 获取播放链接信息
                    url = urljoin(self.host, 'course/%s/task/%s/activity_show' % (course_id, lesson['taskId']))
                    resp = self.session.get(url=url)
                    if '不能访问教学计划' in resp.text:
                        self.logger.error('无权限访问该课程！')
                        return
                    doc_path = re.search('data-url="(.*?)"', resp.text).group(1)
                    doc_url = urljoin(self.host, doc_path)
                    resp = self.session.get(doc_url)
                    # TODO: 下载的文件名在查询参数里，可通过头获得attname，再写准确的
                    file_name = parse_qs(resp.url.split('?')[1])['attname'][0]
                    course = Course(course_id=course_id, course_name=self.my_courses[course_id][0],
                                    chapter_id=chapter_id, chapter_name=chapter_name, section_id=section_id,
                                    section_name=file_name, section_md5=section_md5)
                    course_detail = CourseDetail(id=section_md5, type='doc')
                    self.sql_session.add(course)
                    self.sql_session.add(course_detail)
                    try:
                        self.sql_session.commit()
                    except Exception as e:
                        self.logger.error('插入数据失败：' + str(e))
                        self.sql_session.rollback()
                    """

    def _init_logger(self, log_path=None, file_level=logging.DEBUG, console_level=logging.DEBUG):
        self.logger = logging.getLogger('edusoho')
        self.logger.setLevel(logging.DEBUG)
        # 创建一个handler，用于写入日志文件
        self.log_path = log_path or os.path.join(self.user_data_dir, 'test.log')
        fh = logging.FileHandler(self.log_path, 'a')
        fh.setLevel(file_level)
        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(console_level)
        # 定义handler的输出格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(funcName)s [%(levelname)s] %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # 给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def crawl_my_course(self, use_cache=True):
        need_crawl = False
        if use_cache:
            try:
                self.course_details = pickle.load(open('course', 'rb'))
            except Exception as e:
                self.logger.info('my course list cache file not exist:' + str(e))
                need_crawl = True
        else:
            need_crawl = True
        if need_crawl:
            my_course_url = urljoin(self.host, 'my/courses/learning')
            resp = self.session.get(my_course_url)
            if resp.status_code != 200:
                self.logger.error('无法打开已购课程页面。')
                return
            html = resp.text
            self._resolve_my_course(html)
        try:
            pickle.dump(self.course_details, open('course', 'wb'))
        except Exception as e:
            self.logger.info('cache my course list failed : ' + str(e))

    def _resolve_my_course(self, html_page):
        doc = etree.HTML(text=html_page)
        # 首先处理本页，提取已购课程
        course_elems = doc.xpath('//*[@class="my-course-item cd-mb40 clearfix"]')
        for course in course_elems:
            path = course.xpath('./div[@class="my-course-item__btn"]/a/@href')[0].strip()
            course_id = path.split('/')[-1]
            course_url = urljoin(self.host, path)
            course_name = course.xpath('./div/div/a/text()')[0]
            self.logger.info('课程名：《{}》 课程地址：{}'.format(course_name, course_url))
            self.course_details[course_id] = {'course_name': course_name, 'course_url': course_url}
        # 提取下一页的地址，递归解析
        page_elems = doc.xpath('//*[@class="pagination cd-pagination"]')
        if not page_elems:
            self.logger.error('不能解析下一页列表。')
            return None
        page_elem = page_elems[0]
        for li_elem in page_elem.xpath('./li'):
            if li_elem.xpath('./a/i[@class="cd-icon cd-icon-arrow-right"]'):
                path = li_elem.xpath('./a/@href')[0]
                next_page_url = urljoin(self.host, path)
                self.logger.info('下一页的地址为：' + next_page_url)
                resp = self.session.get(next_page_url)
                if resp.status_code == 200:
                    self._resolve_my_course(resp.text)

logger = logging.getLogger('edusoho')
def decode_key(key):
    """用于解密AES的Key

    :param
        key: 从服务端获取到的key的密文
    :return: 解密后的key
    """
    if len(key) == 20:
        start = int(key[0].lower(), 36) % 7
        algorithm = int(key[start:start + 2], 36) % 3
        if algorithm == 2:
            c9 = ord(key[8]) - ord('a') + (int(key[9]) + 1) * 26 - ord('a')
            c10 = ord(key[10]) - ord('a') + (int(key[11]) + 1) * 26 - ord('a')
            c14 = ord(key[15]) - ord('a') + (int(key[16]) + 1) * 26 - ord('a')
            c15 = ord(key[17]) - ord('a') + (int(key[18]) + 2) * 26 - ord('a')
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
    # logger.info('%s ==dec==> %s' % (key, dec_key))
    return dec_key

def filter_header(m3u8_text):
    ret = None
    try:
        m3u8_obj = m3u8.loads(m3u8_text)
    except ValueError as e:
        pass
    else:
        need_removes = []
        has_header = False
        for segment in m3u8_obj.segments:
            if segment.discontinuity:
                has_header = True
                segment.discontinuity = False
                break
            else:
                need_removes.append(segment)
        if has_header:
            for segment in need_removes:
                m3u8_obj.segments.remove(segment)
        ret = m3u8_obj.dumps()
        ret = TRIM_FULL_KEY_URI.sub(r'\1\2',ret)
        ret = TRIM_USER_INFO.sub(r'\1',ret)
    return ret


def main():
    mySpider = Edusoho(USER, PASSWD)
    mySpider.resolve_my_course()
    pprint(mySpider.course_details)


if __name__ == '__main__':
    main()
