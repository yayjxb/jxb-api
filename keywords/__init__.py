import glob
import os

from common.api import api
from common.base import get_project_path
from data.excel_handle import ReadExcel
from data.template import DataRender

xlsx_files = glob.glob(os.path.join(get_project_path(), 'keywords', '*.xlsx'))


class KeyWordOperator:

    def __init__(self, keyword):
        self.api_data = None
        # 返回的数据名称
        self.rename = None
        self.param = None
        # 替换的模板数据
        self.render = {}
        self.get_keyword_msg(keyword)

    def handle_keyword(self, params):
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
            if tmp and name:
                self.render[tmp] = api.execute(name, in_data, req_data[2], req_data[3])
            elif name and not tmp:
                api.execute(name, in_data, req_data[2], req_data[3])
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
            else:
                ind = case_param.index(j)
                tmp[ind][1] = j
        for data in tmp:
            self.render[data[0]] = data[1]
