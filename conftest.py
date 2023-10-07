import pytest

from common.base import log
from common.init import init
from data.data_handle import DataHandle


def pytest_addoption(parser):
    parser.addoption('--init', action='store', default=False, help='初始化环境选项，默认为否')


def pytest_configure(config):
    get_init = config.getoption('--init')
    if get_init:
        init()


# 修改pytest用例收集规则, 仅收集test开头的.yaml文件
def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".xlsx" and file_path.name.startswith("test"):
        return YamlFile.from_parent(parent, path=file_path)


class YamlFile(pytest.File):
    def collect(self):
        # We need a yaml parser, e.g. PyYAML.
        from data.excel_handle import ReadExcel

        excel_data = ReadExcel(self.path)
        for name in excel_data.sheets:
            yield YamlItem.from_parent(self,
                                       name=name,
                                       case=excel_data.read_rows(name)
                                       )


class YamlItem(pytest.Item):
    def __init__(self, *, case, **kwargs):
        super().__init__(**kwargs)
        self.case = case
        self.case_step = [case[0] for case in self.case]
        self.case_obj = DataHandle()
        # 每个用例步骤的时间记录列表, 在每个call阶段之后增加统计数据
        self.time_consumed = self.case_obj.time_consume

    def runtest(self):
        try:
            self.case_obj.assemble_case(self.case)
        except Exception:
            raise

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if excinfo.type.__name__ != 'AssertionError':
            log.error(excinfo.traceback)
        log.error('error: {}, message: {}', excinfo.type, excinfo.value.args)

    def reportinfo(self):
        return self.path, 0, f"usecase: {self.name}"
