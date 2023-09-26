from common.api import api
from data.template import DataRender
from keywords import KeyWordOperator


class DataHandle:

    def __init__(self):
        self.render_data = {}

    def assemble_case(self, all_case):
        for case in all_case:
            if case[0] is not None:
                if case[2]:
                    case[2] = DataRender.render(case[2], self.render_data)
                case_name = case[1].split('=')
                if len(case_name) == 1:
                    case_name = case_name[0]
                    tmp = ''
                else:
                    tmp, case_name = case_name
                if case_name.startswith('{{') and case_name.endswith('}}'):
                    kwclass = KeyWordOperator(case_name[2:-2])
                    if tmp:
                        self.render_data[tmp] = kwclass.handle_keyword(case[2])
                    else:
                        kwclass.handle_keyword(case[2])
                else:
                    resp = api.execute(case_name, *case[2:5])
                    if tmp:
                        self.render_data[tmp] = resp
