from sqlalchemy.dialects.mysql import MEDIUMTEXT, TEXT, INTEGER, CHAR, BOOLEAN
from sqlalchemy import create_engine, Column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Course(Base):
    __tablename__ = 'course'
    id = Column(INTEGER, primary_key=True)
    course_id = Column(INTEGER)
    course_name = Column(TEXT)
    chapter_id = Column(INTEGER)
    chapter_name = Column(TEXT)
    section_id = Column(INTEGER)
    section_name = Column(TEXT)
    section_md5 = Column(CHAR(127))  # 随机生成


class User(Base):
    __tablename__ = 'user'
    id = Column(INTEGER, primary_key=True)
    username = Column(CHAR(127), unique=True)
    password = Column(CHAR(127))

class UserCourse(Base):
    __tablename__ = 'user_course'
    id = Column(INTEGER, primary_key=True)
    username = Column(CHAR(127))
    course_id = Column(INTEGER)

class CourseDetail(Base):
    __tablename__ = 'course_detail'
    id = Column(INTEGER, primary_key=True)
    section_md5 = Column(CHAR(127))
    type = Column(CHAR(127))
    width = Column(INTEGER)
    m3u8 = Column(MEDIUMTEXT)
    m3u8_full = Column(MEDIUMTEXT)
    aes_key = Column(TEXT)
    has_download = Column(BOOLEAN)


class SqliteSession(object):
    def __init__(self):
        engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3306/course?charset=utf8')
        # engine = create_engine('sqlite:///course.db')
        Session = sessionmaker(bind=engine)
        session = Session()

        User.metadata.create_all(engine)
        Course.metadata.create_all(engine)
        CourseDetail.metadata.create_all(engine)
        self.session = session

    def insert(self):
        pass

# SqliteSession()
