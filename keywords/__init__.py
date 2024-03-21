import glob
import json
import os
import time

from common.api import api
from common.base import log, get_project_path
from data.excel_handle import ReadExcel
from data.template import DataRender

xlsx_files = glob.glob(os.path.join(get_project_path(), 'keywords', '*.xlsx'))


class KeyWordOperator:

    def __init__(self):
        self.api_data = None
        self.time_counter = []
        # 返回的数据名称
        self.rename = None
        self.param = None
        # 替换的模板数据
        self.render = {}
        # 可变参数的传参
        self.kwargs = {}

    def handle_keyword(self, keyword, params):
        print(f'----------关键字: {keyword}----------')
        start = time.time()
        keyword_name = keyword
        # 获取关键字的数据
        self.get_keyword_msg(keyword)
        # 将参数拆分
        self.operate_param(params)
        # 进行关键字的接口调用和数据处理
        for req_data in self.api_data:
            # 处理后的数据
            in_data = DataRender.render(req_data[1], self.render)
            # 处理接口名称
            name = req_data[0].split('=')
            tmp = ''
            if len(name) == 1:
                name = name[0]
            elif len(name) == 2:
                tmp, name = name
            else:
                self.render[self.rename] = in_data
            # 关键字调用关键字
            if name.startswith('{{') and name.endswith('}}'):
                k_name = name[2:-2]
                log.info(f'开始调用关键字: {k_name}')
                self.render[tmp] = self.handle_keyword(k_name, in_data)
                continue
            if tmp:
                self.render[tmp] = api.execute(name, self.request_data_operate(in_data), *req_data[2:5])
            elif name and not tmp:
                api.execute(name, self.request_data_operate(in_data), *req_data[2:5])
        end = time.time()
        log.info(f'关键字: {keyword_name}, 耗时: {end - start}')
        self.time_counter.append((f"关键字: {keyword_name}", end - start))
        print(f'----------关键字: {keyword}----------')
        if self.rename:
            return self.render[self.rename]

    def get_keyword_msg(self, keyword):
        for filename in xlsx_files:
            wb = ReadExcel(filename)
            res = wb.get_keyword_data(keyword)
            if res:
                self.param, self.rename, self.api_data = res
        if not self.api_data:
            raise AssertionError(f'不存在的关键字{keyword}')

    def operate_param(self, params):
        tmp = []
        case_param = params.splitlines() if params else []
        keyword_param = self.param.splitlines() if self.param else []
        for i in keyword_param:
            param = i.split('=')
            if param[0] == '**kwargs':
                continue
            if len(param) == 1:
                tmp.append([param[0], None])
            else:
                tmp.append([param[0], param[1]])
        for j in case_param:
            if '=' in j:
                c_param = j.split('=')
                for data in tmp:
                    if data[0] == c_param[0]:
                        data[1] = c_param[1]
            elif j.startswith('{') and j.endswith('}'):
                if '**kwargs' in keyword_param:
                    try:
                        self.kwargs.update(json.loads(j))
                    except json.JSONDecodeError:
                        raise AssertionError(f'参数格式错误{j}')
                else:
                    log.warning(f'关键字不接收可变传参{j}, 不处理')
            elif j == '**kwargs':
                continue
            else:
                ind = case_param.index(j)
                tmp[ind][1] = j
        for data in tmp:
            self.render[data[0]] = data[1]
        self.render.update(self.kwargs)

    def request_data_operate(self, api_data):
        if '**kwargs' in self.param and '**kwargs' in api_data:
            if api_data.startswith('{') and api_data.endswith('}'):
                return api_data.replace('**kwargs', str(self.kwargs)[1:-1])
            else:
                return api_data.replace('**kwargs', str(self.kwargs))
        else:
            return api_data
