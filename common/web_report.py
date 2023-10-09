import os
import dash
from dash import dash_table, html, dcc
import plotly.graph_objects as go
from common.api import api
from common.extra import check_port


class WebReport:

    def __init__(self, config):
        self.config = config
        self.api_statistics = api.statistics_msg

    def run_server(self, host='0.0.0.0', port='18050'):
        app = dash.Dash()
        self.generate_report(app)
        app.title = 'Web Report'
        check_port(port)
        app.run(host, port)

    def generate_report(self, app):
        app.layout = html.Div(children=[
                self.generate_environment(),
                dcc.Graph(figure=self.generate_pie()),
                dcc.Graph(figure=self.generate_bar())
            ])

    def generate_environment(self, name='名称', value='环境配置'):
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
        x, y = [], []
        for k, v in self.api_statistics.items():
            y.append(k)
            x.append(v['time_stamp'])
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
        labels = ['passed', 'failed']
        values = [0, 0]
        for v in self.api_statistics.values():
            if v['isSuccess']:
                values[0] += 1
            else:
                values[1] += 1
        fig = go.Figure(data=go.Pie(labels=labels, values=values, marker={'colors': ["green", "red"]}))
        fig.update_layout(title_text='执行情况')
        return fig
    