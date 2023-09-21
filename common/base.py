import json
import os
import pymysql
import sshtunnel
from loguru import logger
from requests import Response

import settings
from common.extra import assert_dict_equal


class Assertion:

    @classmethod
    def assert_method(cls, assertion: dict, response: Response):
        if assertion:
            log.info('断言信息: {}', assertion)
            for method in assertion:
                try:
                    getattr(cls, method)(assertion[method], response)
                except AttributeError:
                    log.exception('不存在的断言方式: {}', method)
                    raise

    @staticmethod
    def code(code, response: Response):
        try:
            assert code == response.status_code
            log.debug('断言成功, 状态码: {}', code)
        except AssertionError:
            log.error('断言失败: 期望状态码 {}, 实际状态码 {}', code, response.status_code)
            raise

    @staticmethod
    def body(body, response: Response):
        try:
            assert assert_dict_equal(response.json(), body)
            log.debug('断言成功，body：{}', body)
        except AssertionError:
            log.error('断言失败: 期望值 {}, 实际值 {}', body, response.json())
            raise

    @staticmethod
    def url(url, response: Response):
        try:
            assert url in response.url
            log.debug('断言成功，url：{}', url)
        except AssertionError:
            log.error('断言失败: 期望url {}, 实际url {}', url, response.url)
            raise

    @staticmethod
    def headers(header, response: Response):
        try:
            assert set(header.items()).issubset(response.headers.items())
            log.debug('断言成功，header：{}', header)
        except AssertionError:
            log.error('断言失败: 期望header {}, 实际headers {}', header, response.headers)
            raise


class Log:
    __instance = None

    if not os.path.exists(settings.LOGGING_PATH):
        open(settings.LOGGING_PATH, 'w').close()
    logger.add(settings.LOGGING_PATH,  # 指定文件
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
               encoding='utf-8',
               retention='1 days',  # 设置历史保留时长
               backtrace=True,  # 回溯
               diagnose=True,  # 诊断
               enqueue=True,  # 异步写入
               # rotation="5kb",  # 切割，设置文件大小，rotation="12:00"，rotation="1 week"
               # filter="my_module"  # 过滤模块
               # compression="zip"   # 文件压缩
               )

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Log, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def info(self, msg, *args, **kwargs):
        return logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        return logger.debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        return logger.exception(msg, *args, exc_info=True, **kwargs)


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
        # self.server.close()


# mysql = MySQL(**settings.MYSQL)
log = Log()
