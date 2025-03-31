<<<<<<< HEAD
import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from streamlit.column_config import Column
# ページ設定（ワイドレイアウト）
st.set_page_config(layout="wide")

# 規格範囲の判定関数
def get_limits(target):
    if 2.8 <= target <= 5.0:
        return target - 0.5, target + 0.5
    elif 8.0 <= target <= 35.0:
        return target * 0.9, target * 1.1
    return None, None

# データ処理関数
def process_data(contents):
    decoded = contents.decode('utf-8')
    df = pd.read_csv(io.StringIO(decoded), delimiter="\t")

    df = df[['Table', 'Head', 'Target', 'Result']]
    df['Head'] = df['Head'] + 1
    df['Table'].replace(0, 'A', inplace=True)
    df['Table'].replace(1, 'B', inplace=True)
    df["Lower_Limit"], df["Upper_Limit"] = zip(*df["Target"].map(get_limits))
    df["Index"] = df.groupby(["Table", "Head", "Target"]).cumcount() + 1  # 測定回数のインデックス

    return df

# 異常値の文字色を変更する関数
def color_out_of_limits(val, lower, upper):
    """
    Resultが許容範囲を超えた場合、赤色にする
    """
    if val < lower or val > upper:
        return 'color: red; font-weight: bold'
    return ''

# 統計情報作成関数
def calculate_statistics(df):
    stats_list = []

    for (head, target), group in df.groupby(["Head", "Target"]):
        mean = group["Result"].mean()
        max_value = group["Result"].max()
        min_value = group["Result"].min()
        range_value = max_value - min_value
        sigma_3 = group["Result"].std() * 3

        stats_list.append({
            "Head": head,
            "Target": target,
            "Mean": mean,
            "Max": max_value,
            "Min": min_value,
            "Range": range_value,
            "3σ": sigma_3,
            "Lower_Limit": get_limits(target)[0],
            "Upper_Limit": get_limits(target)[1]
        })

    return pd.DataFrame(stats_list)

# グラフ作成関数
def update_plots(df, selected_table):
    filtered_df = df[df["Table"] == selected_table]
    heads = sorted(filtered_df["Head"].unique())

    plots = []
    for head in heads:
        head_df = filtered_df[filtered_df["Head"] == head]

        # 測定結果をプロットする散布図
        fig = go.Figure()

        for target in head_df["Target"].unique():
            subset = head_df[head_df["Target"] == target]

            fig.add_trace(go.Scatter(
                x=subset["Index"], 
                y=subset["Result"],
                mode="markers", name=f"Target {target}",
                marker=dict(size=4)
            ))

        fig.update_yaxes(range=(0, 40))
        fig.update_layout(
            title=f"Head {head} の測定データ",
            xaxis_title="測定回数",
            yaxis_title="実測値 (Result)",
            template="plotly_white",
            showlegend=False  # 凡例は表示しない
        )

        plots.append(fig)

    return plots

# 箱ひげ図作成関数
def update_boxplot(df, selected_table, selected_head):
    filtered_df = df[(df["Table"] == selected_table) & (df["Head"] == selected_head)]

    fig = go.Figure()

    for target in filtered_df["Target"].unique():
        subset = filtered_df[filtered_df["Target"] == target]

        # 箱ひげ図を作成
        fig.add_trace(go.Box(
            y=subset["Result"],
            x=subset["Target"],
            name=f"Head {selected_head} Target {target}",
            boxmean=True  # 箱ひげ図の中央値を表示
        ))

    fig.update_layout(
        title=f"Head {selected_head} の箱ひげ図",
        xaxis_title="Target",
        yaxis_title="Result",
        template="plotly_white",
        showlegend=False
    )

    return fig

# Streamlit UI設定
st.title("荷重測定結果ビュワー")

# ファイルアップロード
uploaded_file = st.file_uploader("ファイルをアップロード", type=["csv", "txt"])
if uploaded_file is not None:
    df = process_data(uploaded_file.getvalue())

    # Tableの選択
    table_options = df["Table"].unique()
    selected_table = st.selectbox("Tableを選択", table_options)

    # Headの選択
    filtered_df = df[df["Table"] == selected_table]
    head_options = sorted(filtered_df["Head"].unique())
    selected_head = st.selectbox("Headを選択", head_options)

    # 統計情報の表示（選択したHeadのみ）
    stats_df = calculate_statistics(filtered_df)
    stats_df = stats_df[stats_df["Head"] == selected_head].drop(columns=["Head"])  # Head列を削除
    # 文字色を適用するためのスタイル関数
    def highlight_result(s):
        """
        Resultの値が許容範囲を超えている場合に赤色にする
        """
        return [color_out_of_limits(val, lower, upper) for val, lower, upper in zip(s, stats_df["Lower_Limit"], stats_df["Upper_Limit"])]
    # 統計情報と箱ひげ図を横並びに表示
    col1, col2 = st.columns([2, 3])  # 2:3の割合でカラムを作成

    with col1:
        st.subheader(f"統計情報 (Table: {selected_table}, Head: {selected_head})")
        st.dataframe(stats_df.style.apply(highlight_result, subset=["Max", "Min"]), use_container_width=True)

    with col2:
        st.subheader(f"箱ひげ図 ({selected_table}, Head: {selected_head})")
        boxplot_fig = update_boxplot(df, selected_table, selected_head)
        st.plotly_chart(boxplot_fig, use_container_width=True)

    # 測定結果の散布図の表示（4x2レイアウト）
    st.subheader(f"測定結果グラフ ({selected_table})")
    plots = update_plots(df, selected_table)

    cols = st.columns(4)  # 4列のカラムを作成
    for i, fig in enumerate(plots):
        with cols[i % 4]:  # 4列ごとに表示
            st.plotly_chart(fig, use_container_width=True)
=======
import streamlit as st
import pandas as pd
import io
import base64
import plotly.graph_objects as go
import plotly.express as px

# 規格範囲の判定関数
def get_limits(target):
    if 2.8 <= target <= 5.0:
        return target - 0.5, target + 0.5
    elif 8.0 <= target <= 35.0:
        return target * 0.9, target * 1.1
    return None, None

# データ処理関数
def process_data(contents):
    # バイナリデータ（bytes）をデコード
    decoded = contents.decode('utf-8')  # 文字列としてデコード

    # Pandasで読み込み
    df = pd.read_csv(io.StringIO(decoded), delimiter="\t")

    # 必要なカラムを処理
    df = df[['Table', 'Head', 'Target', 'Result']]
    df['Head'] = df['Head'] + 1  # 0スタートを1スタートに
    df['Table'].replace(0, 'A', inplace=True)
    df['Table'].replace(1, 'B', inplace=True)
    df["Lower_Limit"], df["Upper_Limit"] = zip(*df["Target"].map(get_limits))
    df["Index"] = df.groupby(["Table", "Head", "Target"]).cumcount() + 1  # 測定回数のインデックス

    return df

# 統計情報作成関数
def calculate_statistics(df, selected_table):
    if selected_table is None:
        return pd.DataFrame()

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
def update_plots(df, selected_table):
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

        plots.append(fig)

    return plots

# Streamlit UI設定
st.title("測定データ解析ダッシュボード")

# ファイルアップロード
uploaded_file = st.file_uploader("ファイルをアップロード", type=["csv", "txt"])
if uploaded_file is not None:
    # ファイルを処理
    df = process_data(uploaded_file.getvalue())

    # Tableの選択
    table_options = df["Table"].unique()
    selected_table = st.selectbox("Tableを選択", table_options)

    # 統計情報の表示
    stats_df = calculate_statistics(df, selected_table)
    st.subheader(f"統計情報 ({selected_table})")
    st.dataframe(stats_df)

    # グラフの表示
    st.subheader(f"グラフ ({selected_table})")
    plots = update_plots(df, selected_table)
    for fig in plots:
        st.plotly_chart(fig)

>>>>>>> b63745da89442708360c8c2cadf3875195d38bf1
