import time
import pytest

from common.base import log
from common.extra import time_format
from common.init import init
from common.web_report import WebReport
from data.data_handle import DataHandle
import settings


def pytest_addoption(parser):
    parser.addoption('--init', action='store', default=False, help='初始化环境选项，默认为否')
    parser.addoption('--port', action='store', default='18050', help='web报告端口', type=int)


def pytest_configure(config):
    config._metadata['开始时间'] = time_format(time.time())
    config._metadata['项目名称'] = settings.PROJECT_NAME
    config._metadata['项目环境'] = settings.HOST
    get_init = config.getoption('--init')
    config._webreport = WebReport(config)
    config._webreport.start = config._metadata['开始时间'].replace(' ', '-').replace(':', '')
    config.pluginmanager.register(config._webreport)
    if get_init:
        init()


# 修改pytest用例收集规则, 仅收集test开头的.xlsx文件
def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".xlsx" and file_path.name.startswith("test"):
        return ExcelFile.from_parent(parent, path=file_path)


class ExcelFile(pytest.File):
    def collect(self):
        from data.excel_handle import ReadExcel

        excel_data = ReadExcel(self.path)
        # 获取所有的用例信息
        for name in excel_data.sheets:
            all_cases = excel_data.read_rows(name)
            for case in all_cases:
                yield ExcelItem.from_parent(self,
                                            name=name,  # 用例名称
                                            case=case,  # 用例数据
                                            )


class ExcelItem(pytest.Item):
    def __init__(self, *, case, **kwargs):
        super().__init__(**kwargs)
        self.case = case
        self.case_obj = DataHandle()
        # 每个用例步骤的时间记录列表, 在每个call阶段之后增加统计数据
        self.time_consumed = self.case_obj.time_consume

    def runtest(self):
        self.case_obj.assemble_case(self.case)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        log.error('error: {}, message: {}', excinfo.type, excinfo.value.args)
        if not isinstance(excinfo.value, AssertionError):
            return super().repr_failure(excinfo)
        return "\n".join(
            [
                "断言失败",
                f"   详细信息: {excinfo.value.args[0]}",
            ]
        )

    def reportinfo(self):
        return self.path, 0, f"失败的用例: {self.name}, 步骤: {self.case[0]}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()
    report.name = item.name
