import pandas as pd
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
    html.H1("实时数据波形图"),
    dcc.Upload(
        id='upload-data',
        children=html.Button('上传CSV文件'),
        multiple=False
    ),
    dcc.Dropdown(
        id='column-selector',
        multi=True,  # 允许多选
        clearable=False
    ),
    dcc.Graph(id='live-graph')
])

global_df = None

@app.callback(
    [Output('column-selector', 'options'), Output('column-selector', 'value')],
    [Input('upload-data', 'contents')]
)
def update_columns(contents):
    global global_df
    if contents is None:
        return [], []
    global_df = parse_contents(contents)
    columns = global_df.columns.tolist()
    return [{'label': col, 'value': col} for col in columns[2:]], [columns[2]] if len(columns) > 2 else []

@app.callback(
    Output('live-graph', 'figure'),
    [Input('column-selector', 'value')]
)
def update_graph(selected_columns):
    global global_df
    if global_df is None or not selected_columns:
        return {'data': [], 'layout': go.Layout(title='实时数据波形', xaxis={'title': 'time'}, yaxis={'title': 'value'})}
    
    traces = []
    if len(selected_columns) == 1:
        traces.append(go.Scatter(
            x=global_df[global_df.columns[0]],
            y=global_df[selected_columns[0]],
            mode='lines',
            name=selected_columns[0]
        ))
    else:
        for col in selected_columns:
            mean_value = global_df[col].mean()
            traces.append(go.Scatter(
                x=global_df[global_df.columns[0]],
                y=global_df[col] - mean_value,
                mode='lines',
                name=f'{col} (去均值)'
            ))
    
    return {'data': traces, 'layout': go.Layout(title='实时数据波形', xaxis={'title': 'time'}, yaxis={'title': 'value'})}

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
