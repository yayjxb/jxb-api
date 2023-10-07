import json
from requests import Response

from common.base import log
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
            assert assert_dict_equal(response.json(), json.loads(body)), '响应中不存在断言数据'
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
