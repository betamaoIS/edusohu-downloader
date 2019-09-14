#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import errno
import json
import os
import re
import subprocess
from multiprocessing.dummy import Pool

import ffmpy

from datastorage import SqliteSession, CourseDetail, Course
from logger import logger
from settings import FFMPEG, FFMPEG_LOGLEVEL, MAXTHREADS
from utils import escape

TRIM_FULL_KEY_URI = re.compile(r'(#EXT-X-KEY:METHOD=AES-128,URI=")\d+/clef/(\w{32})')


def main():
    ...


def gen_course_data(root='out'):
    """将数据库里的数据导出到本地（导出清晰度最高的数据）

    :param root: 输出文件的根目录
    :return:
    """
    sql_session = SqliteSession().session
    # 获取所有课程
    course_objs = sql_session.query(Course).all()
    orgin_dir = [root, ]
    for course_obj in course_objs:
        # 获取课程文件路径
        course_dir = orgin_dir[:]
        course_dir.append('{}-{}'.format(course_obj.course_id, course_obj.course_name))
        course_dir.append('第{}章-{}'.format(course_obj.chapter_id, course_obj.chapter_name))
        course_dir.append('第{}节-{}.m3u8'.format(course_obj.section_id, course_obj.section_name))
        course_dir = map(lambda s: escape(s).strip(), course_dir)
        course_m3u8_path = '/'.join(course_dir)

        course_dir = os.path.dirname(course_m3u8_path)
        if not os.path.exists(course_m3u8_path):
            try:
                os.makedirs(course_dir, exist_ok=True)
            except Exception as e:
                logger.error('{}-{}'.format(course_dir, e))
        # 写入数据
        section_md5 = course_obj.section_md5
        course_detail = sql_session.query(CourseDetail.m3u8, CourseDetail.aes_key).filter(
            CourseDetail.section_md5 == section_md5).order_by(
            CourseDetail.width.desc()).first()
        m3u8_text = course_detail.m3u8  # TRIM_FULL_KEY_URI.sub(r'\1\2',course_detail.m3u8)
        with open(course_m3u8_path, 'w') as f:
            f.write(m3u8_text)
        path_key = json.loads(course_detail.aes_key)
        key_path, key = path_key.popitem()
        course_key_path = os.path.join(course_dir, key_path)
        os.makedirs(os.path.dirname(course_key_path), exist_ok=True)
        with open(course_key_path, 'w') as f:
            f.write(key)


def download(m3u8_path, mp4_path=None, ffmpeg_path=FFMPEG, ffmpeg_loglevel=FFMPEG_LOGLEVEL):
    """执行下载操作，需要依赖ffmpeg

    :param m3u8_path: 要下载的m3u8文件的绝对路径
    :param mp4_path: 输出文件路径，默认输出和m3u8同级目录同名文件。
    :param ffmpeg_path: ffmpeg可执行程序的路径
    :param ffmpeg_loglevel: 日志级别
    :return:
    """
    cache = m3u8_path.replace('.m3u8', '.has_down')
    if os.path.exists(cache):
        return
    if mp4_path is None:
        mp4_path = m3u8_path.replace('.m3u8', '.mp4')
    ffmpeg_cmd = ffmpy.FFmpeg(
        ffmpeg_path,
        '-y -loglevel {}'.format(ffmpeg_loglevel),
        inputs={m3u8_path: '-allowed_extensions ALL -protocol_whitelist "file,http,crypto,tcp,https,tls"'},
        outputs={mp4_path: '-c copy'}
    )
    # logger.info(ffmpeg_cmd.cmd)
    try:
        try:
            process = subprocess.Popen(
                ffmpeg_cmd.cmd,
                shell=True,
                cwd=os.path.dirname(m3u8_path)
            )
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise ffmpy.FFExecutableNotFoundError("Executable '{0}' not found".format(ffmpeg_path))
            else:
                raise
        out = process.communicate()
        if process.returncode != 0:
            raise ffmpy.FFRuntimeError(ffmpeg_cmd.cmd, process.returncode, out[0], out[1])
    except Exception as e:
        logger.error('{} ---> {}'.format(m3u8_path, e))
    else:
        try:
            with open(cache, 'w') as f:
                f.write('hello world')
        except Exception as e:
            logger.error('{} ---> {}'.format(cache, e))
    logger.info('{} download finish...'.format(m3u8_path))


def download_all(root, thread_num=MAXTHREADS):
    """遍历目录下载所有文件。

    :param root: 包含m3u8文件的根目录
    :return:
    """
    m3u8s = []
    for root_, _, files in os.walk(root):
        for file_ in files:
            if not file_.endswith('.m3u8'):
                continue
            path = os.path.join(root_, file_)
            m3u8s.append(os.path.abspath(path))
    with Pool(thread_num) as pool:
        pool.map(download, m3u8s)


if __name__ == '__main__':
    # gen_course_data()
    download_all('out')
