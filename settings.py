"""
配置文件
"""
PROJECT_NAME = 'jxb-api'

# 控制台IP地址和端口

HOST = '172.16.10.14'
BASE_URL = 'https://172.16.10.14:8000/api'

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

