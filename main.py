import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import pandas as pd
import io
import base64
import plotly.graph_objects as go
import dash_bootstrap_components as dbc  # dash-bootstrap-componentsをインポート

# Dashアプリケーションの初期化
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])  # Bootstrapテーマを使用

# レイアウトの定義
app.layout = html.Div([
    html.H1("測定データ解析ダッシュボード", className="text-center"),
    dbc.Row([
        dbc.Col(dcc.Upload(id="upload-data", children=html.Button("ファイルをアップロード"), multiple=False), width=12),
    ], justify="center"),
    html.Div(id="file-name", className="text-center mt-3"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id="table-dropdown", placeholder="Tableを選択", multi=False), width=6)
    ], justify="center"),
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
    df['Head'] = df['Head'] + 1  # 0スタートを1スタートに
    df['Table'].replace(0, 'A', inplace=True)
    df['Table'].replace(1, 'B', inplace=True)
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

# 統計情報作成関数
def calculate_statistics(selected_table):
    if selected_table is None:
        return []

    filtered_df = df[df["Table"] == selected_table]
    stats_list = []

    for (table, head, target), group in filtered_df.groupby(["Table", "Head", "Target"]):
        mean = group["Result"].mean()
        max_value = group["Result"].max()
        min_value = group["Result"].min()
        range_value = max_value - min_value
        sigma_3 = group["Result"].std() * 3

        stats_list.append({
            "Table": table,
            "Head": head,
            "Target": target,
            "Mean": round(mean,2),
            "Max": round(max_value,2),
            "Min": round(min_value,2),
            "Range": round(range_value,2),
            "3σ": round(sigma_3,2)
        })

    stats_df = pd.DataFrame(stats_list)
    return stats_df

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

            fig.add_trace(go.Scatter(
                x=subset["Index"], y=subset["Result"],
                mode="markers", name=f"Target {target}",
                marker=dict(size=3)
            ))
            fig.update_yaxes(range=(0, 40))
            fig.update_layout(showlegend=False)

        fig.update_layout(
            title=f"Head {head} の測定データ",
            xaxis_title="測定回数",
            yaxis_title="実測値 (Result)",
            template="plotly_white"
        )

        plots.append(dcc.Graph(figure=fig))

    # 4x2のレイアウトでグラフを配置
    cols = []
    for i in range(0, len(plots), 4):
        cols.append(dbc.Row([dbc.Col(plot, width=3) for plot in plots[i:i + 4]]))  # 横4個ずつ表示

    # 統計情報のテーブル作成
    stats_df = calculate_statistics(selected_table)

    # テーブルの作成
    table_list = []
    for head in range(1, 9):  # Head1〜Head8
        head_stats = stats_df[stats_df["Head"] == head]
        table = dash_table.DataTable(
            id=f"statistics-table-head-{head}",
            columns=[
                {"name": col, "id": col} for col in ["Target", "Mean", "Max", "Min", "Range", "3σ"]
            ],
            data=head_stats[["Target", "Mean", "Max", "Min", "Range", "3σ"]].to_dict("records"),
            style_table={"height": "300px", "overflowY": "auto"},
            style_cell={'textAlign': 'center'},
            style_header={'fontWeight': 'bold'}
        )
        table_list.append(dbc.Col(table, width=3, style={'margin': '5px'}))  # 横4個ずつ表示

    # 4x2のレイアウトでテーブルを表示
    table_rows = []
    for i in range(0, len(table_list), 4):
        table_rows.append(dbc.Row(table_list[i:i + 4]))

    return cols + table_rows

if __name__ == '__main__':
    app.run(debug=True)
