import json

import requests
from requests import Response
import settings
import urllib3

from common.base import log
from common.assertion import Assertion
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

    def execute(self, case_info):
        response = self.request_method(case_info.get('request'))
        Assertion.assert_method(case_info.get('assert', []), response)
        if case_info.get('extract', None):
            log.debug('提取信息：{}', case_info.get('extract'))
            return DataRender.extractor(*case_info.get('extract')[:-1], response)
        if case_info.get('caller', None):
            caller_info = case_info.get('caller')
            DataRender.caller(caller_info)


api = Api()
