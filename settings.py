"""
配置文件
"""

# 控制台IP地址和端口
import os

HOST = '192.168.116.128'
BASE_URL = 'http://192.168.116.128:3000/'

# 超管账号
ACCOUNT = {
    'Email': 'jsh',
    'Password': '123456',
    '2fa': 'QWNBLWV2QNHYZR2DDJLMNJ72REFNAYUW'
}

# MySQL连接配置
MYSQL = {
    'host': HOST,
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'y9k2'
}

# ssh连接配置
SSH = {
    'user': 'root',
    'key': '~/.ssh/id_rsa'
}

# 当前运行环境，'TEST'测试环境，'PRO'线上环境
ENVIRONMENT = 'TEST'

# 日志配置
LOGGING_PATH = os.path.dirname(__file__).split('autoApi')[0] + 'autoApi/log/autoApi.log'
