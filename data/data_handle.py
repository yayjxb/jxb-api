import json
import os


from common.api import api
from common.base import get_project_path
from data.excel_handle import ReadExcel
from data.template import DataRender

keyword_file = os.path.join(get_project_path(), 'keywords.xlsx')
url_file = os.path.join(get_project_path(), 'urls.xlsx')


class DataHandle:

    def __init__(self):
        self.keyword = ReadExcel(keyword_file)
        self.url = ReadExcel(url_file)
        self.render_data = {}

    def assemble_case(self, all_case):
        for case in all_case:
            if case[0] is not None:
                if case[1].startswith('{{') and case[1].endswith('}}'):
                    k_msg = self.keyword.get_keywords(case[1][2:-2])
                    self.handle_keyword(k_msg, case[2])
                else:
                    case_info = self.api_data_build(f"{case[1]}({case[2]})", case[3])
                    resp = api.execute(case_info)
                    if case_info.get('extract', None):
                        self.render_data[case_info.get('extract')[-1]] = resp

    def handle_keyword(self, keyword_data, case_data):
        self.handle_keyword_param(keyword_data[1], case_data)
        api_data = self.handle_api_extract(*keyword_data[2:4])
        for req_api in api_data:
            exec_api = DataRender.render(req_api[0], self.render_data)
            exec_extract = req_api[1] if len(req_api) > 1 else ''
            case_info = self.api_data_build(exec_api, exec_extract)
            resp = api.execute(case_info)
            if case_info.get('extract', None):
                self.render_data[case_info.get('extract')[-1]] = resp

    def handle_keyword_param(self, keyword_param: str, case_param):
        tmp = []
        case_param = case_param.splitlines() if case_param else []
        keyword_param = keyword_param.splitlines() if keyword_param else []
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
            self.render_data[data[0]] = data[1]

    @classmethod
    def handle_api_extract(cls, api_data, extract):
        """
        将api和提取表达式关联
        """
        api_data = [[i] for i in api_data.splitlines()]
        if extract:
            extract = extract.splitlines()
            for i, data in enumerate(extract):
                api_data[i].append(data)
        return api_data

    def api_data_build(self, api_data, extract):
        req_data = {'request': {}}
        api_name = api_data[:api_data.find('(')]
        extract_name = ''
        if '=' in api_name:
            extract_name, api_name = api_name.split('=')
        api_data = api_data[api_data.find('(')+1:-1].split('::')
        all_url_data = self.url.get_keywords(api_name)
        req_data['request']['method'] = all_url_data[1]
        req_data['request']['url'] = all_url_data[2]
        op_data = json.loads(all_url_data[3].replace('\n', '').replace(' ', '').replace("'", '"').replace("None", 'null'))
        if extract:
            req_data['extract'] = [*extract.split('::'), extract_name]
        if len(api_data) == 1:
            if api_data[0] != 'None':
                op_data.update(json.loads(api_data[0]))
            if req_data['request']['method'].lower() in ['get', 'delete']:
                req_data['request']['params'] = op_data
            else:
                req_data['request']['json'] = op_data
        else:
            if api_data[1] != 'None':
                op_data.update(json.loads(api_data[1]))
            req_data['request'][api_data[0].lower()] = op_data
        return req_data


case1 = ReadExcel(os.path.join(get_project_path(), 'demo.xlsx'))
for sheet in case1.sheets:
    da = DataHandle()
    da.assemble_case(case1.read_rows(sheet))
