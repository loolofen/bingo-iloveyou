import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px
from datetime import datetime, timedelta
import random

# --- 業界最強視覺：電競黑金終端 UI ---
st.set_page_config(page_title="BINGO 數據戰略終端", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle, #1a1a2e 0%, #020205 100%); color: #00d4ff; }
    .stMetric { background: rgba(0, 212, 255, 0.05); border: 1px solid #00d4ff; border-radius: 10px; padding: 15px; box-shadow: 0 0 15px #00d4ff33; }
    .recommend-card { 
        background: linear-gradient(135deg, #0f0f1b 0%, #252545 100%); 
        border: 1px solid #00d4ff; color: #fff; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border-left: 5px solid #00d4ff;
    }
    .stButton>button { 
        background: linear-gradient(90deg, #00d4ff, #0055ff); color: white !important;
        font-weight: 900; border-radius: 5px; height: 3em; border: none; width: 100%; text-transform: uppercase;
    }
    .ball-box {
        display: inline-flex; width: 32px; height: 32px; background: #000;
        border: 1px solid #444; border-radius: 4px; justify-content: center;
        align-items: center; margin: 2px; font-size: 0.85rem; font-family: 'Courier New';
    }
    .strong-text { color: #ff0055; font-weight: bold; } /* 高於 30% */
    .weak-text { color: #00ff88; font-weight: bold; }   /* 低於 20% */
    .super-highlight { background: #00d4ff; color: #000; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心抓取函數 ---
def get_auzo_data(date_str):
    url = f"https://lotto.auzo.tw/bingobingo/list_{date_str}.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('tr.bingo_row')
        data = []
        for r in rows:
            p = r.select_one('td.BPeriod').find('b').text.strip()
            balls = [int(d.text) for d in r.find_all('td')[1].find_all('div') if d.text.isdigit()]
            if len(balls) >= 20: data.append({"期數": p, "號碼": balls})
        return data
    except: return []

# --- 初始化數據池 ---
if 'pool' not in st.session_state:
    st.session_state.pool = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# --- UI 介面開始 ---
st.title("⚡ BINGO STRATEGY TERMINAL")
st.caption("📍 Tainan Annan | 大數據機率位移演算系統")

# 控制區
col1, col2 = st.columns([1, 2])
with col1:
    if st.button("🛰️ 同步最近三天數據"):
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]
        all_data = []
        for d in dates: all_data.extend(get_auzo_data(d))
        st.session_state.pool = all_data
        
if st.session_state.pool:
    with col2:
        sample_size = st.select_slider("分析樣本數 (期)", options=[50, 100, 200, 500], value=100)
    
    # 執行計算
    data = st.session_state.pool[:sample_size]
    counts = Counter([n for d in data for n in d['號碼']])
    stats = []
    for i in range(1, 81):
        freq = counts.get(i, 0) / len(data)
        label = "🔥 強勢" if freq >= 0.30 else ("❄️ 弱勢" if freq <= 0.20 else "⚖️ 中性")
        stats.append({"號碼": i, "頻率": freq, "標籤": label, "次數": counts.get(i, 0)})
    
    df = pd.DataFrame(stats)
    strong_list = df[df['標籤'] == "🔥 強勢"]['號碼'].tolist()
    medium_list = df[df['標籤'] == "⚖️ 中性"]['號碼'].tolist()
    weak_list = df[df['標籤'] == "❄️ 弱勢"]['號碼'].tolist()

    # --- 核心顯示區 ---
    tab1, tab2, tab3 = st.tabs(["🎯 戰略建議", "📊 數據看板", "🔎 號碼驗證"])

    with tab1:
        play_mode = st.radio("玩法切換", ["三星", "四星", "五星"], horizontal=True)
        
        # 重新選號按鈕
        if st.button("🎲 重新生成建議組合"):
            st.rerun()

        st.subheader("🚀 前四名戰略組合推薦")
        cols = st.columns(2)
        
        # 選號邏輯：依據玩法動態從強中弱池中隨機抽取最優分佈
        for i in range(4):
            if play_mode == "三星":
                res = random.sample(strong_list, 2) + random.sample(medium_list, 1)
            elif play_mode == "四星":
                res = random.sample(strong_list, 2) + random.sample(medium_list, 2)
            else:
                res = random.sample(strong_list, 3) + random.sample(medium_list, 1) + random.sample(weak_list, 1)
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="recommend-card">
                    <div style="font-size:0.8rem; color:#00d4ff;">RANK {i+1} OPTION</div>
                    <div style="font-size:1.5rem; letter-spacing:3px; font-weight:bold;">{', '.join([f'{n:02d}' for n in sorted(res)])}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.subheader("📈 全號碼機率分佈 (1-80)")
        # 顯示所有號碼標籤
        st.write("🔴 紅色：強勢 (>30%) | 🟢 綠色：弱勢 (<20%)")
        
        ball_html = ""
        for index, row in df.iterrows():
            color_class = "strong-text" if row['標籤'] == "🔥 強勢" else ("weak-text" if row['標籤'] == "❄️ 弱勢" else "")
            ball_html += f'<div class="ball-box {color_class}">{int(row["號碼"]):02d}</div>'
            if row['號碼'] % 10 == 0: ball_html += "<br>"
        st.markdown(ball_html, unsafe_allow_html=True)
        
        fig = px.bar(df, x='號碼', y='頻率', color='標籤', color_discrete_map={"🔥 強勢": "#ff0055", "⚖️ 中性": "#444", "❄️ 弱勢": "#00ff88"})
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🔍 原始數據校驗 (最近期數)")
        for d in data[:10]:
            st.write(f"期數: {d['期數']}")
            ball_str = "".join([f'<div class="ball-box">{n:02d}</div>' for n in sorted(d['號碼'])])
            st.markdown(ball_str, unsafe_allow_html=True)

st.info("💡 系統提示：本工具採用 25% 基線演算法，強勢區號碼代表其出現機率比理論值高出 5% 以上。")
