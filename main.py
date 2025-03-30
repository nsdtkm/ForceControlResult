import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import pandas as pd
import io
import base64
import plotly.graph_objects as go

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("測定データ解析ダッシュボード"),
    dcc.Upload(id="upload-data", children=html.Button("ファイルをアップロード"), multiple=False),
    html.Div(id="file-name"),
    dcc.Dropdown(id="table-dropdown", placeholder="Tableを選択", multi=False),
    html.Div(id="scatter-plots")
])

# 規格範囲の判定関数
def get_limits(target):
    if 2.8 <= target <= 5.0:
        return target - 0.5, target + 0.5
    elif 8.0 <= target <= 35.0:
        return target * 0.9, target * 1.1
    return None, None

# データ処理関数
def process_data(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter="\t")

    df = df[['Table', 'Head', 'Target', 'Result']]
    df["Lower_Limit"], df["Upper_Limit"] = zip(*df["Target"].map(get_limits))
    df["Index"] = df.groupby(["Table", "Head", "Target"]).cumcount() + 1  # 測定回数のインデックス

    return df

# コールバック：ファイルアップロードとTable選択時にデータ更新
@app.callback(
    [Output("file-name", "children"),
     Output("table-dropdown", "options"),
     Output("table-dropdown", "value"),
     Output("scatter-plots", "children")],
    [Input("upload-data", "contents"),
     Input("table-dropdown", "value")],
    prevent_initial_call=True
)
def update_dashboard(contents, selected_table):
    global df

    # コールバックのトリガーを判定
    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if trigger_id == "upload-data":
        if contents is None:
            return "", [], None, []
        df = process_data(contents)

        table_options = [{"label": f"Table {t}", "value": t} for t in df["Table"].unique()]
        default_table = df["Table"].unique()[0]  # 最初のTableをデフォルト選択
        return "ファイル: " + contents[:30] + "...", table_options, default_table, update_plots(default_table)

    elif trigger_id == "table-dropdown":
        return dash.no_update, dash.no_update, dash.no_update, update_plots(selected_table)

    return dash.no_update

# グラフ作成関数
def update_plots(selected_table):
    if selected_table is None:
        return []

    filtered_df = df[df["Table"] == selected_table]
    heads = sorted(filtered_df["Head"].unique())

    plots = []
    for head in heads:
        head_df = filtered_df[filtered_df["Head"] == head]

        fig = go.Figure()

        for target in head_df["Target"].unique():
            subset = head_df[head_df["Target"] == target]
            # lower, upper = subset["Lower_Limit"].iloc[0], subset["Upper_Limit"].iloc[0]

            fig.add_trace(go.Scatter(
                x=subset["Index"], y=subset["Result"],
                mode="markers", name=f"Target {target}",
                marker=dict(size=3)
            ))

            # fig.add_trace(go.Scatter(
            #     x=[subset["Index"].min(), subset["Index"].max()],
            #     y=[lower, lower], mode="lines",
            #     name=f"Lower {target}", line=dict(color="red", dash="dash")
            # ))
            # fig.add_trace(go.Scatter(
            #     x=[subset["Index"].min(), subset["Index"].max()],
            #     y=[upper, upper], mode="lines",
            #     name=f"Upper {target}", line=dict(color="red", dash="dash")
            # ))

        fig.update_layout(
            title=f"Head {head} の測定データ",
            xaxis_title="測定回数",
            yaxis_title="実測値 (Result)",
            template="plotly_white"
        )

        plots.append(dcc.Graph(figure=fig))

    return plots

if __name__ == '__main__':
    app.run(debug=True)
