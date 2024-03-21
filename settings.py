"""
配置文件
"""
PROJECT_NAME = 'jxb-api'

# 控制台IP地址和端口

HOST = '172.16.10.14'
BASE_URL = 'https://172.16.10.14:8000/api'
HEADERS = {'Content-Type': 'application/json'}

# 日志文件文件名称, 在log文件夹下(自动创建), 设置为False则不生成日志文件
LOG_FILE = 'api.log'
