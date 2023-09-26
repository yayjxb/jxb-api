import json
import os

import requests
from requests import Response
import settings
import urllib3

from common.base import log, get_project_path
from common.assertion import Assertion
from data.excel_handle import ReadExcel
from data.template import DataRender


class Api:
    _instance = None
    request_token = None

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
            self.set_api_token(DataRender.extractor('jsonpath', "$.data", response)[0])
        log.info('请求url信息:{}', response.request.url)
        log.info('请求体信息:{}', response.request.body)
        log.info('响应信息：{}', response.text)
        return response

    def execute(self, name, data, extract=None, assertion=None):
        case_info = self.api_data_build(name, data, extract, assertion)
        response = self.request_method(case_info.get('request'))
        Assertion.assert_method(case_info.get('assert', []), response)
        if case_info.get('extract', None):
            log.debug('提取信息：{}', case_info.get('extract'))
            return DataRender.extractor(*case_info.get('extract'), response)
        if case_info.get('caller', None):
            caller_info = case_info.get('caller')
            DataRender.caller(caller_info)

    def api_data_build(self, name, data, extract, assertion):
        req_data = {'request': {}}
        url = ReadExcel(os.path.join(get_project_path(), 'urls.xlsx'))
        all_url_data = url.get_keywords(name)
        req_data['request']['method'] = all_url_data[1]
        req_data['request']['url'] = all_url_data[2]
        op_data = json.loads(
            all_url_data[3].replace('\n', '').replace(' ', '').replace("'", '"').replace("None", 'null'))
        if extract:
            req_data['extract'] = extract.split('::')
        if data:
            api_data = data.split('::')
            if len(api_data) == 1:
                if api_data[0] != 'None':
                    op_data.update(json.loads(api_data[0]))
                if req_data['request']['method'].lower() in ['get', 'delete']:
                    req_data['request']['params'] = op_data
                else:
                    req_data['request']['json'] = op_data
            elif len(api_data) == 2:
                if api_data[1] != 'None':
                    op_data.update(json.loads(api_data[1]))
                req_data['request'][api_data[0].lower()] = op_data
        return req_data


api = Api()

