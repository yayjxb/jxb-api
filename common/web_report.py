import dash
from dash import dash_table, html, dcc
import plotly.graph_objects as go
from common.api import api
from common.extra import check_port


class WebReport:

    def __init__(self, config):
        # Config对象
        self.config = config
        # api接口统计信息[[接口名称, 耗时, 是否成功], [接口名称, 耗时, 是否成功]]
        self.api_statistics = api.statistics_msg
        # 日志捕获信息[[用例名, 日志内容], [用例名, 日志内容]]
        self.capture_log = []

    def run_server(self, host='0.0.0.0', port=18050):
        app = dash.Dash()
        self.generate_report(app)
        app.title = 'Web Report'
        check_port(port)
        app.run(host, port)

    def generate_report(self, app):
        """生成网页布局"""
        app.layout = html.Div(children=[
                self.generate_environment(),
                dcc.Graph(figure=self.generate_pie()),
                dcc.Graph(figure=self.generate_bar()),
                html.Div(children=["详细日志结果", 
                    html.P(children=[
                        # 两个a标签, 展示和隐藏所有log
                        html.A("Show all logs", href="javascript:document.querySelectorAll(\".log\").forEach((detail) => {detail.open = true;})"), " / ",
                        html.A("Hide all logs", href="javascript:document.querySelectorAll(\".log\").forEach((detail) => {detail.open = false;})")]),
                        # 处理log展示
                        self.log_operator()
                ])
            ])

    def generate_environment(self, name='名称', value='环境配置'):
        """表格展示环境配置"""
        env_data = self.config._metadata
        result = []
        for k, v in env_data.items():
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
        x, y = [], []
        for v in self.api_statistics:
            y.append(v[0])
            x.append(v[1])
        y = self.name_repeat_rename(y)
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
        values = [0, 0]
        for v in self.api_statistics:
            if v[2]:
                values[0] += 1
            else:
                values[1] += 1
        fig = go.Figure(data=go.Pie(labels=labels, values=values, marker={'colors': ["green", "red"]}))
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
        return html.Div(result)
    
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
        detail_style = {"padding": "0.2em", "word-break": "break-word", "border": "1px solid #e6e6e6", "font": "14px monospace"}
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
                    k_index = logs.index(log, i+1)
                    children.append(self.generate_details(log, logs[i+1:k_index]))
                else:
                    children.append(self.context_log_operator(log))
        return all_details
    
    def log_operator(self):
        children = []
        div = html.Div(children=children)
        for details in self.capture_log:
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

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.record_capstdout(report)

    def pytest_unconfigure(self):
        self.run_server(port=self.config.getoption('--port'))
