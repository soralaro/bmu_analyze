import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# 读取 CSV 文件
file_path = '/data/bmu_analyze/bmu_data/_20250307-105259_20kW.csv'
df = pd.read_csv(file_path)
columns = df.columns.tolist()  # 获取所有列名

# 确保时间列转换为时分秒格式
df[columns[0]] = pd.to_datetime(df[columns[0]]).dt.strftime('%H:%M:%S')

# 创建 Dash 应用
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("实时数据波形图"),
    dcc.Dropdown(
        id='column-selector',
        options=[{'label': col, 'value': col} for col in columns[2:]],  # 排除前两列
        value=[columns[2]],  # 默认选择第三列
        multi=True,  # 允许多选
        clearable=False
    ),
    dcc.Graph(id='live-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # 每秒刷新一次
        n_intervals=0
    )
])

@app.callback(
    Output('live-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('column-selector', 'value')]
)
def update_graph(n, selected_columns):
    # 重新读取 CSV（适用于数据不断更新的情况）
    df = pd.read_csv(file_path)
    df = df.tail(1000)  # 只显示最新的 1000 条数据
    df[columns[0]] = pd.to_datetime(df[columns[0]]).dt.strftime('%H:%M:%S')  # 转换时间格式
    
    traces = []
    if len(selected_columns) == 1:
        # 如果只选择了一列，直接绘制原始数据
        traces.append(go.Scatter(
            x=df[columns[0]],  # 第一列作为时间轴
            y=df[selected_columns[0]],  # 原始数据
            mode='lines',
            name=selected_columns[0]
        ))
    else:
        # 多列情况下，先减去均值再绘制
        for col in selected_columns:
            mean_value = df[col].mean()  # 计算均值
            traces.append(go.Scatter(
                x=df[columns[0]],  # 第一列作为时间轴
                y=df[col] - mean_value,  # 数据减去均值
                mode='lines',
                name=f'{col} (去均值)'
            ))
    
    return {'data': traces, 'layout': go.Layout(title='实时数据波形', xaxis={'title': 'time'}, yaxis={'title': 'value'})}

if __name__ == '__main__':
    app.run_server(debug=True)