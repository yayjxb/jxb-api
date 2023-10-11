import copy
import json
import time
from common.api import api
from common.base import log
from data.template import DataRender
from keywords import KeyWordOperator


class DataHandle:

    def __init__(self):
        self.render_data = {}
        self.time_consume = []

    def assemble_case(self, case):
        if len(case) > 5 and case[5]:
            for param in case[5].splitlines():
                self.parameterize_operators(param)
                self.run_case(case)
        else:
            self.run_case(case)

    def run_case(self, case_info):
        case = copy.deepcopy(case_info)
        if case[0] is not None:
            start = time.time()
            log.info(f"当前正在执行的步骤: {case[0]}")
            if case[2]:
                case[2] = DataRender.render(case[2], self.render_data)
            case_name = case[1].split('=')
            if len(case_name) == 1:
                case_name = case_name[0]
                tmp = ''
            else:
                tmp, case_name = case_name
            if case_name.startswith('{{') and case_name.endswith('}}'):
                keyword_name = case_name[2:-2]
                keyword_class = KeyWordOperator()
                log.info(f'开始调用关键字: {keyword_name}')
                if tmp:
                    self.render_data[tmp] = keyword_class.handle_keyword(keyword_name, case[2])
                else:
                    keyword_class.handle_keyword(keyword_name, case[2])
                self.time_consume.extend(keyword_class.time_counter)
            else:
                resp = api.execute(case_name, *case[2:5])
                if tmp:
                    self.render_data[tmp] = resp
            total_time = time.time() - start
            log.info(f"步骤: {case[0]}, 耗时:{total_time}")
            self.time_consume.append((case[0], total_time))

    def parameterize_operators(self, params):
        log.info(f"参数化数据: {params}")
        try:
            params_dict = json.loads(params)
        except json.JSONDecodeError:
            raise AssertionError(f'参数化数据格式错误{params}')
        self.render_data.update(params_dict)
