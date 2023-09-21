import ast
import json
import os

from jinja2 import Template

variable_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/global.json')
case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'testcase')


def data_render(template: str, data: dict) -> str:
    """变量替换, 将全局变量中的值替换到测试用例中"""
    tm = Template(template)
    new_data = tm.render(data)
    return new_data


def save_variable(var: dict):
    try:
        with open(variable_path, 'r+') as f:
            date = json.loads(f.read())
            date.update(var)
            with open(variable_path, 'w') as f1:
                f1.write(json.dumps(date, ensure_ascii=False))
    except FileNotFoundError:
        with open(variable_path, 'w') as f:
            f.write(json.dumps(var))


def read_variable(name=None):
    with open(variable_path, 'r+') as f:
        if name is None:
            return json.loads(f.read())
        else:
            var = json.loads(f.read())
            return var[name]


def read_case(file_path):
    with open(file_path, 'r+') as f:
        return str(json.loads(f.read()))


def get_file():
    """获取所有测试用例文件"""
    file_list = []
    for dirname in os.walk(case_path):
        for file in dirname[2]:
            if file.endswith('.json'):
                file_list.append(os.path.join(dirname[0], file))
    return file_list


def get_request():
    """获取所有测试用例"""
    req = []
    for file in get_file():
        data = data_render(read_case(file), read_variable())
        req.append(ast.literal_eval(data))
    return req


def get_data(file=None):
    """组装所有的测试用例"""
    result = []
    if file is None:
        data = get_request()
    else:
        data = ast.literal_eval(data_render(read_case(file), read_variable()))
        if isinstance(data, list):
            for j in data:
                result.append(j)
        else:
            result.append(data)
        return result
    for i in data:
        if isinstance(i, list):
            for j in i:
                result.append(j)
        else:
            result.append(i)
    return result


print(get_data())
