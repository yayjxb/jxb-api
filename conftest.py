import json
from datetime import datetime
from operator import methodcaller
from typing import Optional

import pytest
from _pytest.compat import NOTSET
from _pytest.fixtures import FuncFixtureInfo
from _pytest.hookspec import hookspec
from _pytest.python import PyobjMixin

import common
from common.api import api
from common.base import log
from common.init import init
from py.xml import html


def pytest_addoption(parser):
    parser.addoption('--init', action='store', default=False, help='初始化环境选项，默认为否')


def pytest_configure(config):
    get_init = config.getoption('--init')
    if get_init:
        init()


# 收集测试用例、改变用例的执行顺序, 根据用例传入的order参数进行排序, 值越大优先级越高, 给每个用例添加上mark和fixture
def pytest_collection_modifyitems(items, config):
    # items是所有的用例列表
    items.sort(key=lambda item: item.order, reverse=True)
    for item in items:
        if item.mark:
            if isinstance(item.mark, list):
                for m in item.mark:
                    item.add_marker(eval(f'pytest.mark.{m}'))
            else:
                item.add_marker(eval(f'pytest.mark.{item.mark}'))
        if item.fix:
            if isinstance(item.mark, list):
                for f in item.mark:
                    item.add_marker(eval(f'pytest.mark.usefixtures("{f}")'))
            else:
                item.add_marker(eval(f'pytest.mark.usefixtures("{item.fix}")'))


# 修改pytest用例收集规则, 仅收集test开头的.yaml文件
def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml" and file_path.name.startswith("test"):
        return YamlFile.from_parent(parent, path=file_path)


class YamlFile(pytest.File):
    def collect(self):
        # We need a yaml parser, e.g. PyYAML.
        import yaml

        raw = yaml.unsafe_load(self.path.open(encoding='utf-8'))
        for name, case in raw.items():
            yield YamlItem.from_parent(self,
                                       name=name,
                                       case=case,
                                       order=case.get('order', 0),
                                       mark=case.get('mark', None),
                                       fix=case.get('fixture', None)
                                       )


class YamlItem(pytest.Item):
    def __init__(self, *, case, order, mark, fix, **kwargs):
        super().__init__(**kwargs)
        self.case = case
        self.order = order
        self.mark = mark
        self.fix = fix
        # self.fixturenames = [].append(self.fix)
        # self._fixtureinfo: FuncFixtureInfo = FuncFixtureInfo((), *self.session._fixturemanager.getfixtureclosure(('aa',), self.parent))

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def runtest(self):
        try:
            api.execute(self.case)
        except Exception:
            raise

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        log.error(excinfo.traceback)
        log.error('error: {}, message: {}', excinfo.type, excinfo.value.args)

    def reportinfo(self):
        return self.path, 0, f"usecase: {self.name}"


# 编辑报告标题
def pytest_html_report_title(report):
    report.title = "api autotest report"


# 编辑摘要信息
# def pytest_html_results_summary(prefix, summary, postfix):
#     prefix.extend([html.p("foo: bar")])


# 测试结果表格
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th("Time", class_="sortable time", col="time"))
    cells.pop()


def pytest_html_results_table_row(report, cells):
    cells.insert(1, html.td(report.start))
    cells.pop()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # 获取钩子方法的调用结果，返回一个result对象
    out = yield

    # 从钩子方法的调用结果中获取测试报告
    report = out.get_result()
    report.nodeid = report.nodeid.encode("unicode_escape").decode("utf-8")
    if report.when == 'setup':
        item.add_report_section('setup', 'stdin', json.dumps(item.case))
    for i in item.user_properties:
        if i[0] == 'start_time':
            report.start = i[1]


def pytest_runtest_setup(item):
    item.user_properties.append(('start_time', datetime.now()))


def pytest_fixture_setup(fixturedef, request):
    print('22222')


@pytest.fixture(scope="function", autouse=True)
def aa():
    print('111111')

