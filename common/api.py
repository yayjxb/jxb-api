import json

import requests
from requests import Response
import settings
import urllib3

from common.base import log, Assertion
from data.template import DataHandle

urllib3.disable_warnings()


class Api:
    _instance = None
    request_token = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Api, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.session = requests.session()

    @classmethod
    def set_api_token(cls, token=None):
        cls.request_token = token

    def get_headers(self, headers):
        header = {'X-Access-Token': self.request_token}
        if headers:
            header.update(headers)
        return header

    def request_method(self, request_option: dict) -> Response:
        response = self.session.request(
            url=settings.BASE_URL + request_option.get("url", None),
            method=request_option.get("method", "POST"),
            params=request_option.get("params", None),
            # data=json.dumps(request_option.get("data", None)),
            json=request_option.get("json", None),
            files=request_option.get("files", None),
            headers=self.get_headers(request_option.get("headers", None)),
            cookies=request_option.get("cookies", None),
            timeout=request_option.get("timeout", None),
            cert=request_option.get("cert", None)
        )
        log.info('请求url信息:{}', response.request.url)
        log.info('请求体信息:{}', response.request.body)
        log.info('响应信息：{}', response.text)
        return response

    def execute(self, case_data):
        case_info = DataHandle.render(case_data)
        log.info('渲染后的测试数据{}', case_info)
        response = self.request_method(case_info.get('request'))
        Assertion.assert_method(case_info.get('assert'), response)
        if case_info.get('extract', None):
            log.debug('提取信息：{}', case_info.get('extract'))
            DataHandle.extractor(*case_info.get('extract', None), response)
        if case_info.get('caller', None):
            caller_info = case_info.get('caller')
            DataHandle.caller(caller_info)


api = Api()
