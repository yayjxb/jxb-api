import json
import os

import requests
from requests import Response
from common.extra import str_format
import settings
import urllib3

from common.base import log, get_project_path
from common.assertion import Assertion
from data.excel_handle import ReadExcel
from data.template import DataRender


class Api:
    _instance = None
    request_token = None
    statistics_msg = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Api, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        urllib3.disable_warnings()
        self.session = requests.session()

    @classmethod
    def set_api_token(cls, token=None):
        cls.request_token = token

    def get_headers(self, headers):
        header = {'Authorization': self.request_token}
        if headers:
            header.update(headers)
        return header

    def request_method(self, request_option: dict) -> Response:
        response = self.session.request(
            url=settings.BASE_URL + request_option.get("url", ''),
            method=request_option.get("method", "POST"),
            params=request_option.get("params", None),
            data=request_option.get("data", None),
            json=request_option.get("json", None),
            files=request_option.get("files", None),
            headers=self.get_headers(request_option.get("headers", None)),
            # cookies=request_option.get("cookies", None),
            timeout=request_option.get("timeout", None),
            # cert=request_option.get("cert", None),
            verify=False
        )
        if request_option.get("url", '') == '/login':
            self.set_api_token(DataRender.extractor("$.data", response=response)[0])
        log.info('请求url信息:{}', response.request.url)
        log.info('请求体信息:{}', response.request.body)
        log.info('响应信息：{}', response.text)
        log.info('接口耗时: {} s', response.elapsed)
        return response

    def execute(self, name, data, extract=None, assertion=None):
        case_info = self.api_data_build(name, data, extract, assertion)
        # 未传入接口名称, 处理数据后直接返回
        if not name:
            return case_info
        response = self.request_method(case_info.get('request'))
        tmp_result = [case_info.get('request')['url'], response.elapsed.total_seconds(), True]
        self.statistics_msg.append(tmp_result)
        try:
            Assertion.assert_method(case_info.get('assert', {}), response)
        except AssertionError:
            tmp_result[2] = False
            raise
        if case_info.get('extract', None):
            log.debug('提取信息：{}', case_info.get('extract'))
            return DataRender.extractor(case_info.get('extract'), response=response)

    def api_data_build(self, name, data, extract, assertion):
        log.debug(f'处理接口数据, 接口名称:{name}, 接口数据:{data}')
        req_data = {'request': {}}
        url = ReadExcel(os.path.join(get_project_path(), 'urls.xlsx'))
        # 若没有传入接口名称, 认为仅仅做数据处理
        try:
            if name:
                all_url_data = url.get_keywords(name)
                req_data['request']['method'] = all_url_data[1]
                req_data['request']['url'] = all_url_data[2]
                op_data = json.loads(str_format(all_url_data[3]))
            else:
                op_data = json.loads(str_format(data))
        except json.JSONDecodeError:
            raise AssertionError(f'传递的接口数据格式错误')
        if extract:
            req_data['extract'] = extract
        if data and name:
            api_data = data.split('::')
            if len(api_data) == 1:
                if api_data[0]:
                    try:
                        op_data.update(json.loads(str_format(api_data[0])))
                    except json.JSONDecodeError:
                        raise AssertionError(f'传递的参数格式错误{api_data[0]}')
                if req_data['request']['method'].lower() in ['get', 'delete']:
                    req_data['request']['params'] = op_data
                else:
                    req_data['request']['json'] = op_data
            elif len(api_data) == 2:
                if api_data[1]:
                    try:
                        op_data.update(json.loads(str_format(api_data[1])))
                    except json.JSONDecodeError:
                        raise AssertionError(f'传递的参数格式错误{api_data[1]}')
                req_data['request'][api_data[0].lower()] = op_data
        # 只有数据没有接口名称, 认为不做接口信息处理, 直接返回数据
        elif data and not name:
            return op_data
        else:
            if req_data['request']['method'].lower() in ['get', 'delete']:
                req_data['request']['params'] = op_data
            else:
                req_data['request']['json'] = op_data
        if assertion:
            req_data['assert'] = {}
            all_assert_data = assertion.splitlines()
            for line in all_assert_data:
                method, expression = line.split('::')
                req_data['assert'][method] = expression
        return req_data


api = Api()
