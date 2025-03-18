import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
import base64
import io

# 创建 Dash 应用
app = dash.Dash(__name__)

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]]).dt.strftime('%H:%M:%S')  # 转换时间格式
    return df

app.layout = html.Div([
    html.H1("实时数据分析"),
    
    # 上传文件
    dcc.Upload(id='upload-data', children=html.Button('上传CSV文件'), multiple=False),
    html.Div(id='file-name-display', style={'marginTop': '10px', 'fontWeight': 'bold', 'color': 'blue'}),
    dcc.Store(id="last-file-name"),  # 记录上次的文件名
    
    # 选择数据列
    dcc.Dropdown(id='column-selector', multi=True, clearable=False, placeholder="选择要分析的列"),
    
    # 数据平滑
    html.Label("数据平滑 (滑动窗口大小)"),
    dcc.Slider(id='smoothing-slider', min=1, max=50, step=1, value=1, marks={i: str(i) for i in range(1, 51, 10)}),
    
    # 波形图
    dcc.Graph(id='live-graph'),
    
    # 频谱分析
    dcc.Graph(id='fft-graph'),
    
    # 导出数据
    html.Button("导出数据", id="export-btn", style={'marginTop': '10px'}),
    dcc.Download(id="download-dataframe-csv")
])

global_df = None

@app.callback(
    [Output('column-selector', 'options'), Output('column-selector', 'value'),
     Output("last-file-name", "data"), Output("file-name-display", "children")],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_columns(contents, filename):
    global global_df
    if contents is None:
        return [], [], dash.no_update, "未选择文件"
    
    global_df = parse_contents(contents)
    columns = global_df.columns.tolist()
    
    # 显示上传的文件名
    file_display = f"已上传文件: {filename}" if filename else "文件名未知"
    
    return [{'label': col, 'value': col} for col in columns[2:]], [columns[2]] if len(columns) > 2 else [], filename, file_display

@app.callback(
    Output('live-graph', 'figure'),
    [Input('column-selector', 'value'), Input('smoothing-slider', 'value')]
)
def update_graph(selected_columns, smooth_window):
    global global_df
    if global_df is None or not selected_columns:
        return {'data': [], 'layout': go.Layout(title='实时数据波形', xaxis={'title': 'time'}, yaxis={'title': 'value'})}
    
    traces = []
    for col in selected_columns:
        data = global_df[col]
        
        # 平滑数据 (滑动窗口平均)
        if smooth_window > 1:
            data = data.rolling(window=smooth_window, min_periods=1).mean()
        
        traces.append(go.Scatter(
            x=global_df[global_df.columns[0]],
            y=data,
            mode='lines',
            name=f'{col} (平滑:{smooth_window})'
        ))
    
    return {'data': traces, 'layout': go.Layout(title='实时数据波形', xaxis={'title': 'time'}, yaxis={'title': 'value'})}

@app.callback(
    Output('fft-graph', 'figure'),
    [Input('column-selector', 'value')]
)
def update_fft(selected_columns):
    global global_df
    if global_df is None or not selected_columns:
        return {'data': [], 'layout': go.Layout(title='频谱分析', xaxis={'title': '频率'}, yaxis={'title': '幅度'})}
    
    traces = []
    for col in selected_columns:
        data = global_df[col].dropna().values
        n = len(data)
        
        # 计算 FFT
        fft_values = np.abs(np.fft.fft(data))
        frequencies = np.fft.fftfreq(n)
        
        # 只显示正频率部分
        half_n = n // 2
        traces.append(go.Scatter(
            x=frequencies[:half_n],
            y=fft_values[:half_n],
            mode='lines',
            name=f'{col} 频谱'
        ))
    
    return {'data': traces, 'layout': go.Layout(title='频谱分析', xaxis={'title': '频率'}, yaxis={'title': '幅度'})}

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("export-btn", "n_clicks")],
    prevent_initial_call=True
)
def export_data(n_clicks):
    global global_df
    if global_df is None:
        return None
    
    return dcc.send_data_frame(global_df.to_csv, filename="exported_data.csv")

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
