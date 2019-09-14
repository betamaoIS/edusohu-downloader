import logging
import os

from settings import LOG_DIR
logger = logging.getLogger('edusoho')
logger.setLevel(logging.DEBUG)
# 创建一个handler，用于写入日志文件
log_path = os.path.join(LOG_DIR, 'test.log')

fh = logging.FileHandler(log_path, 'a')
fh.setLevel(logging.DEBUG)
# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 定义handler的输出格式
formatter = logging.Formatter(
    '[%(asctime)s] %(funcName)s [%(levelname)s] %(message)s'
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)