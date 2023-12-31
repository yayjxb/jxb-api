import os
from pathlib import Path
import sys

import pymysql
import sshtunnel
from loguru import logger

import settings
from common.extra import check_file_exists


def get_project_path(cur_path=None):
    """
    获取当前项目的根路径
    """
    project = settings.PROJECT_NAME
    if cur_path is None:
        cur_path = os.getcwd()
    parent_path = os.path.dirname(cur_path)
    if cur_path == parent_path:
        raise AssertionError(log.error(f"未在目录中检索到项目名:{project}"))
    elif os.path.join(parent_path.lower(), project) in cur_path.lower():
        root_path = os.path.abspath(cur_path)
    elif os.path.join(parent_path.upper(), project) in cur_path.upper():
        root_path = os.path.abspath(cur_path)
    else:
        root_path = get_project_path(cur_path=parent_path)
    return root_path


class Log:
    __instance = None
    log_path = Path(get_project_path()) / 'log' / settings.LOG_FILE if settings.LOG_FILE else sys.stdout

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Log, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.log = logger
        self.init_log()

    def init_log(self):
        self.log.remove()
        check_file_exists(self.log_path)
        self.log.add(sys.stdout,
                     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | "
                            "{process.name:<12}| "  # 进程名
                            "{thread.name:<11}| "  # 线程名
                            "<cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
                     # colorize=True,    # 显示颜色
                     # enqueue=True,  # 异步写入
                     )
        if self.log_path:
            logger.add(self.log_path,  # 指定文件
                       format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <7}</level> | "
                              "{process.name:<12}| "  # 进程名
                              "{thread.name:<11}| "  # 线程名
                              "<cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
                       # 模块名:方法名:行号,
                       encoding='utf-8',
                       retention='1 days',  # 设置历史保留时长
                       backtrace=True,  # 回溯
                       diagnose=True,  # 诊断
                       # enqueue=True,  # 异步写入
                       # rotation="5kb",  # 切割，设置文件大小，rotation="12:00"，rotation="1 week"
                       # filter="my_module"  # 过滤模块
                       # compression="zip"   # 文件压缩
                       )


class MySQL:

    def __init__(self, host, port=3306, user='root', password='', database='y9k2'):
        sshtunnel.SSH_TIMEOUT = 5.0
        self.server = sshtunnel.SSHTunnelForwarder(
            ssh_address_or_host=(host, 22),  # 指定ssh登录的跳转机的address
            ssh_username=user,  # 跳转机的用户
            ssh_pkey='~/.ssh/id_rsa',
            remote_bind_address=('127.0.0.1', port)
        )
        self.server.start()
        self.db = pymysql.connect(host='127.0.0.1', port=self.server.local_bind_port, user=user, password=password,
                                  database=database, connect_timeout=5)
        self.cursor = self.db.cursor()

    def execute(self, sql):
        self.cursor.execute(sql)
        if sql.split()[0].lower() in ['update', 'insert']:
            self.db.commit()
        result = self.cursor.fetchall()
        return result

    def check_connection(self):
        try:
            self.db.ping()
            return True
        except Exception as e:
            print(e.__traceback__.tb_frame)
            raise ConnectionError('mysql connection error')

    def __del__(self):
        self.cursor.close()


# mysql = MySQL(**settings.MYSQL)
log = Log().log
