"""
初始化环境使用，例如：MySQL的数据库清理，初始超管账号生成，相关配置文件生成等等操作
在pytest调用配置文件的钩子函数时进行判断，是否命令行传参要求进行初始化
"""
import json

from requests import Response

import settings
from common.api import Api
from common.extra import *
from data.template import DataHandle


def save_cookie():
    res = login()
    DataHandle.save_variable(get_dict('cookie', f'Session={res.cookies.values()[0]}'))


def save_org():
    res = get_org()
    org = json_extract(json.loads(res.text), '$..OrgTree.OrgId')
    print(org)
    DataHandle.save_variable(get_dict('orgId', org[0]))


def login() -> Response:
    login_data = {
        'url': 'AdminSignInAction',
        'params': {
            'Email': settings.ACCOUNT['Email'],
            'Password': settings.ACCOUNT['Password']
        }
    }
    fa_date = {
        'url': 'CtUserSignInCheckGoogleAuthAction',
        'params': {
            'googleCode': fa_code(settings.ACCOUNT['2fa'])
        }
    }
    Api.request_method(login_data)
    res = Api.request_method(fa_date)
    return res


def get_org() -> Response:
    data = {
        'url': 'CtAdminOrgDetail',
        'headers': {
            'cookie': DataHandle.read_variable('cookie')
        },
        'json': {'OrgId': ''}
    }
    res = Api.request_method(data)
    return res


def init():
    print('初始化环境完成')
    # save_cookie()
    # save_org()


# init()
