import web
import json
from datastorage import SqliteSession, User, UserCourse, CourseDetail, Course
from sqlalchemy import and_, distinct
from web.template import render

urls = (
    '/login', 'Login',
    '/logout', 'logout',
    '/(.*).m3u8', 'M3U8',
    '/course/player/(.*)', 'Play',
    r'/(\d+/clef/\w{32})', 'AesKey',
    r'/listCourse', 'ListCourse',
    r'/courseDetails/(\d+)', 'ListCourseDetail',
    '.*', 'ListCourse'
)
app = web.application(urls, globals())
# 创建session
if web.config.get('_session'):
    session = web.config._session
else:
    session = web.session.Session(app, web.session.DiskStore('sessions'), {'loggedin': False, 'username': '','course_ids':[]})
    web.config._session = session


def logged(fuc):
    def wrap(*args):
        if not session.loggedin:
            web.seeother('/login')
        else:
            return fuc(*args)
    return wrap

def hav_course(func):
    def wrap(*args):

        if not session.loggedin:
            web.seeother('/login')
        else:
            return func(*args)
    return wrap

class PageBase(object):
    def POST(self, *args):
        web.seeother('/login')

    def GET(self):
        web.seeother('/login')


class Login(PageBase):
    def POST(self):
        paras = web.input()
        password = paras.password
        username = paras.username
        sql_session = SqliteSession().session
        try:
            sql_session.query(User).filter(and_(User.username == username, User.password == password)).one()
        except Exception as e:
            return "Those login details don't work." + username + password
        else:
            session.loggedin = True
            session.username = paras.username
            raise web.seeother('/listCourse')

    def GET(self):
        if session.loggedin:
            return session.username
        # if logged():
        #    ...
        # else:
        template = render('template')
        return template.login()
        # ...


class Logout(PageBase):
    def GET(self):
        ...


class ListCourse(PageBase):
    @logged
    def GET(self):
        sql_session = SqliteSession().session
        user_all_course = sql_session.query(distinct(UserCourse.course_id)).filter(
            UserCourse.username == session.username).all()
        course_ids = list(map(lambda s: s[0], user_all_course))
        session.course_ids = course_ids
        res = sql_session.query(distinct(Course.course_id), Course.course_name).filter(
            Course.course_id.in_(course_ids)).all()
        return render('template').listCourse(res)


class ListCourseDetail(object):
    @logged
    def GET(self, course_id):
        if course_id.isdigit() and int(course_id) not in session.course_ids:
            return "<h1>ennnnnnn... what's your problem...</a>"
        sql_session = SqliteSession().session
        res = sql_session.query(Course.course_name, Course.chapter_id, Course.chapter_name, Course.section_id,
                                Course.section_name, Course.section_md5).filter(Course.course_id == course_id).order_by(
            Course.chapter_id.asc()).order_by(Course.section_id.asc()).all()
        return render('template').listCourseDetail(res)


class Play(object):
    @logged
    def GET(self, section_md5):
        return render('template').player(section_md5)


class M3U8(object):
    @logged
    def GET(self, section_md5):
        sql_session = SqliteSession().session
        res = sql_session.query(CourseDetail.m3u8).filter(CourseDetail.section_md5 == section_md5).order_by(
            CourseDetail.width.desc()).first()
        if res:
            res = res[0]
        return res


class AesKey(object):
    @logged
    def GET(self, key):
        sql_session = SqliteSession().session
        res = sql_session.query(CourseDetail.aes_key).filter(CourseDetail.aes_key.like('%' + key + '%')).first()
        if res:
            data = json.loads(res[0])
            res = data.popitem()[1]
        return res


if __name__ == '__main__':
    app.run()
