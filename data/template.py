"""
数据驱动核心
动态参数替换和全局变量管理
"""
import json
import os
from operator import methodcaller

import jinja2
import jsonpath

from common.base import log
from common.extra import md5_string


class DataRender:
    variable_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'global.json')

    @classmethod
    def render(cls, case_info, render_data=None):
        """
        动态参数替换，将用例中的{{}}中的所有内容进行替换

        :param case_info: 用例信息
        :param render_data:
        :return: 替换后的用例
        """
        log.debug(f'原始数据: {case_info}')
        template = jinja2.Template(case_info)
        template.globals['Func'] = Func
        if render_data:
            log.debug(f"模板: {render_data}")
            response = template.render(render_data)
        else:
            response = template.render(cls.read_variable())
        log.debug(f'模板替换后的数据: {response}')
        return response

    @classmethod
    def save_variable(cls, var: dict):
        """将变量保存到全局变量中"""
        try:
            with open(cls.variable_path, 'r+', encoding='utf-8') as f:
                date = json.loads(f.read())
                date.update(var)
                with open(cls.variable_path, 'w', encoding='utf-8') as f1:
                    f1.write(json.dumps(date, ensure_ascii=False))
        except FileNotFoundError:
            with open(cls.variable_path, 'w') as f:
                f.write(json.dumps(var))
        except TypeError:
            log.exception('提取后的变量必须保存')

    @classmethod
    def read_variable(cls, name=None):
        """
        获取某个全局变量的值，若没有指定则获取所有的全局变量

        :param name: 变量名称
        :return: 变量的值或全部变量
        """
        try:
            with open(cls.variable_path, 'r+', encoding='utf-8') as f:
                if name is None:
                    return json.loads(f.read())
                else:
                    var = json.loads(f.read())
                    return var[name]
        except KeyError:
            log.error('不存在的全局变量：{}', name)

    @classmethod
    def extractor(cls, path=None, option='jsonpath', response=None):
        """
        提取器，对响应结果进行提取

        :param option: 提取方式，暂时仅支持python 和 jsonpath
        :param path: 提取的表达式
        :param response: 响应对象
        :return: 无返回值
        """
        if option == 'python':
            ext = eval(str(response.json()) + path)
        elif option == 'jsonpath':
            ext = jsonpath.jsonpath(response.json(), path)
        else:
            ext = None
            print(f'暂不支持的提取方式: {option}')
        log.debug(f'提取结果: {ext}')
        return ext

    @classmethod
    def caller(cls, caller_info):
        new_call_list = [caller_info[0]]
        for i in caller_info[1:]:
            if 'global.' in i:
                name = i.split('.')[1]
                new_call_list.append(cls.read_variable(name))
            else:
                new_call_list.append(i)
        log.info('自定义函数调用{}', new_call_list)
        methodcaller(*new_call_list)(Func)


class Func:

    @classmethod
    def md5(cls, string):
        return md5_string(string)

    @classmethod
    def set_token(cls, token):
        from common.api import Api
        Api.set_api_token(token)
