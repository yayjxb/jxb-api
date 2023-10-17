import glob
import json
import os
from pathlib import Path

import dash
from dash import dash_table, html, dcc, Output, Input
import plotly.graph_objects as go
from common.api import api
from common.base import get_project_path
from common.extra import check_port, check_file_exists


class WebReport:

    def __init__(self, config):
        self.metadata = None
        self.all_log = None
        self.pass_count = None
        self.api_time = None
        self.api_name = None
        # Config对象
        self.config = config
        # api接口统计信息[[接口名称, 耗时, 是否成功], [接口名称, 耗时, 是否成功]]
        self.api_statistics = api.statistics_msg
        # 日志捕获信息[[用例名, 日志内容], [用例名, 日志内容]]
        self.capture_log = []
        self.start: str = ''
        self.history_dir = Path(get_project_path()) / 'history'

    def run_server(self, host='0.0.0.0', port=18050):
        app = dash.Dash()
        app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content'),
        ])
        app.title = 'Web Report'

        # 回调函数, 根据url渲染html内容
        @app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
        def display_page(pathname):
            if pathname == '/':
                return self.index_page()
            else:
                return self.generate_report(pathname)

        check_port(port)
        app.run(host, port)

    def index_page(self):
        """首页展示历史报告连接"""
        children = []
        layout = html.Div([
                    html.H2(children='历史报告', id='title'),
                    html.Ul(children),
                ])
        file_list = self.get_history_file()
        # 展示前五次, 需要多展示修改遍历次数即可
        for file in file_list[:5]:
            name = Path(file).name.split('.')[0]
            children.append(
                        html.Li(html.A(name, href=f'{name}/'))
                      )
        return layout

    def generate_report(self, name):
        """生成网页布局"""
        self.read_file(name)
        layout = html.Div(children=[
            self.generate_environment(),
            dcc.Graph(figure=self.generate_pie()),
            dcc.Graph(figure=self.generate_bar()),
            html.Div(
                children=[
                    "详细日志结果",
                    html.P(children=[
                        # 两个a标签, 展示和隐藏所有log
                        html.A(
                            "Show all logs",
                            href="javascript:document.querySelectorAll('.log').forEach((detail)=>{detail.open=true;})"
                        ),
                        " / ",
                        html.A(
                            "Hide all logs",
                            href="javascript:document.querySelectorAll('.log').forEach((detail)=>{detail.open=false;})"
                        )]),
                    # 处理log展示
                    self.log_operator()
                ])
        ])
        return layout

    def generate_environment(self, name='名称', value='环境配置'):
        """表格展示环境配置"""
        result = []
        for k, v in self.metadata.items():
            result.append({name: k, value: str(v)})
        table = dash_table.DataTable(
            data=result,
            style_header={
                'backgroundColor': '#c8ced7',
                'fontWeight': 'bold',
            },
            style_cell={
                'textAlign': 'left'
            },
        )
        return table

    def generate_bar(self):
        """横向柱状图, 展示接口耗时"""
        x = self.api_time
        y = self.name_repeat_rename(self.api_name)
        fig = go.Figure(go.Bar(
            x=x,
            y=y,
            orientation='h',
            marker={
                "color": "#ff7700",
            },
        ))
        fig.update_layout(title_text='接口耗时', barmode='stack', yaxis={'categoryorder': 'total ascending'})
        return fig

    def generate_pie(self):
        """饼状图, 统计耗时"""
        labels = ['passed', 'failed']
        values = self.pass_count
        fig = go.Figure(go.Pie(labels=labels, values=values, marker={'colors': ["green", "red"]}))
        fig.update_layout(title_text='执行情况')
        return fig

    def name_repeat_rename(self, li):
        """处理名称重复"""
        count = {}
        res = []
        for i in li:
            if i in count:
                count[i] += 1
            else:
                count[i] = 0
            if i in res:
                res.append(f'{i}({count[i]})' if count[i] != 0 else i)
            else:
                res.append(i)
        return res

    def context_log_operator(self, context):
        """将日志的详细内容的进行处理"""
        result = []
        if isinstance(context, str):
            result.extend(self.html_operator(context, '\n'))
            result = self.html_operator(result, 'INFO')
            result = self.html_operator(result, 'WARNING')
            result = self.html_operator(result, 'ERROR')
        else:
            for txt in context:
                result.extend(self.context_log_operator(txt))
        return html.Div(result, style={"white-space": "pre-wrap"})

    def html_operator(self, context, sign):
        result = []
        if isinstance(context, str):
            all_logs = context.split(sign)
            if sign == '\n':
                for line in all_logs:
                    result.extend([line, html.Br()])
            elif sign == 'INFO':
                for line in all_logs:
                    result.extend([line, html.Span(sign, style={"color": "blue"})])
            elif sign == 'WARNING':
                for line in all_logs:
                    result.extend([line, html.Span(sign, style={"color": "orange"})])
            elif sign == 'ERROR':
                for line in all_logs:
                    result.extend([line, html.Span(sign, style={"color": "red"})])
            if sign != '\n':
                result = result[:-1]
        elif isinstance(context, list):
            for txt in context:
                result.extend(self.html_operator(txt, sign))
        else:
            result.append(context)
        return result

    def generate_details(self, name, logs, style: dict = None):
        """生成html格式的log日志"""
        detail_style = {
            "padding": "0.2em",
            "word-break": "break-word",
            "border": "1px solid #e6e6e6",
            "font": "14px monospace"
        }
        if style:
            detail_style.update(style)
        children = []
        all_details = html.Details(children=children, style=detail_style, className="log")
        children.append(html.Summary(name))
        k_index = 0
        for i, log in enumerate(logs):
            if i == 0:
                children.append(self.context_log_operator(log))
            if i > k_index:
                # 将关键字的日志单独拆分处理, 下一次的日志遍历从关键字后的日志开始
                if log.startswith("关键字: "):
                    k_index = logs.index(log, i + 1)
                    children.append(self.generate_details(log, logs[i + 1:k_index]))
                else:
                    children.append(self.context_log_operator(log))
        return all_details

    def log_operator(self):
        children = []
        div = html.Div(children=children)
        for details in self.all_log:
            # 将捕获到的日志进行拆分处理
            name = details[0]
            log = details[1].split('----------')
            de = self.generate_details(name, log)
            children.append(de)
        return div

    def record_capstdout(self, report):
        """将用例对象传递的数据接收存储"""
        node = report.name
        if node in [i[0] for i in self.capture_log]:
            for log in self.capture_log:
                if log[0] == node:
                    log[1] += report.capstdout
        else:
            self.capture_log.append([node, report.capstdout])

    def write_file(self, save_file):
        all_result = {
            'pass_count': [0, 0],
            'api_name': [],
            'api_time': [],
            'all_log': self.capture_log,
            'metadata': self.config._metadata
        }
        for v in self.api_statistics:
            all_result['api_name'].append(v[0])
            all_result['api_time'].append(v[1])
            if v[2]:
                all_result['pass_count'][0] += 1
            else:
                all_result['pass_count'][1] += 1
        save_file.write_text(json.dumps(all_result))

    def read_file(self, name):
        file_path = self.history_dir / f'{name[1:-1]}.json'
        all_result = json.loads(file_path.read_text())
        self.all_log = all_result['all_log']
        self.api_name = all_result['api_name']
        self.api_time = all_result['api_time']
        self.pass_count = all_result['pass_count']
        self.metadata = all_result['metadata']

    def check_file_number(self):
        """检查历史报告文件数量, 超过指定数量则删除文件"""
        file_list = self.get_history_file()
        file_list.sort(reverse=True)
        # 超过10个文件, 则删除最老的历史记录
        if len(file_list) > 10:
            for file in file_list[10:]:
                Path(file).unlink()

    def get_history_file(self) -> list:
        history_file = os.path.join(self.history_dir, '*.json')
        file_list = glob.glob(history_file)
        file_list.sort(reverse=True)
        return file_list

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.record_capstdout(report)

    def pytest_sessionfinish(self):
        save_file = self.history_dir / f'{self.start}.json'
        check_file_exists(save_file)
        self.write_file(save_file)
        self.check_file_number()

    def pytest_unconfigure(self):
        self.run_server(port=self.config.getoption('--port'))
