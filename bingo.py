import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
import random
import math
import plotly.express as px

# --- 1. 賽博黑金 UI 配置 ---
st.set_page_config(page_title="BINGO 數據指揮中心 V10", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #000; color: #00ffcc; font-family: 'Consolas', monospace; }
    [data-testid="stSidebar"] { background-color: #050510; border-right: 1px solid #00ffcc; }
    .neon-card { 
        background: rgba(10, 10, 20, 0.9); border: 1px solid #00ffcc; 
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
    }
    .stButton>button { background: #00ffcc; color: #000 !important; font-weight: 900; border-radius: 4px; height: 3.5em; width: 100%; border: none;}
    .ball-style { display: inline-flex; width: 32px; height: 32px; background: #111; border: 1px solid #444; border-radius: 5px; justify-content: center; align-items: center; margin: 2px; font-size: 0.85rem; font-weight: bold; }
    .highlight-s { border-color: #ff0055; color: #ff0055; }
    .highlight-w { border-color: #00ff88; color: #00ff88; }
    .history-hit { color: #ff00ff; font-size: 0.8rem; font-weight: bold; margin-top: 5px; }
    .ratio-tag { background: #333; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; color: #00ffcc; border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據抓取核心 ---
@st.cache_data(ttl=300)
def fetch_bingo_data(days=3):
    today = datetime.now()
    results = []
    for i in range(days):
        d_str = (today - timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://lotto.auzo.tw/bingobingo/list_{d_str}.html"
        try:
            res = requests.get(url, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('tr.bingo_row')
            for r in rows:
                p = r.select_one('td.BPeriod').find('b').text.strip()
                divs = r.find_all('td')[1].find_all('div')
                nums = [int(d.text) for d in divs if d.text.isdigit()]
                if len(nums) >= 20: results.append({"期數": p, "號碼": sorted(nums), "日期": d_str})
        except: continue
    return results

def nCr(n, r):
    if r < 0 or r > n: return 0
    return math.comb(n, r)

# --- 3. 側邊欄：僅保留核心設定與機率參考 ---
if 'full_data' not in st.session_state: st.session_state.full_data = []

with st.sidebar:
    st.header("🛰️ 系統控制台")
    if st.button("🔄 同步最近三日資料庫"):
        st.session_state.full_data = fetch_bingo_data(3)
    
    if st.session_state.full_data:
        sample_size = st.slider("分析深度 (期)", 30, len(st.session_state.full_data), 100)
        data = st.session_state.full_data[:sample_size]
        all_nums = [n for d in data for n in d['號碼']]
        counts = Counter(all_nums)
        df_stats = pd.DataFrame([{"號碼": i, "頻率": counts.get(i, 0)/len(data), "次數": counts.get(i, 0)} for i in range(1, 81)])
        df_stats['標籤'] = df_stats['頻率'].apply(lambda x: "強" if x >= 0.30 else ("弱" if x <= 0.20 else "中"))
        
        s_pool = list(df_stats[df_stats['標籤'] == "強"]['號碼'])
        m_pool = list(df_stats[df_stats['標籤'] == "中"]['號碼'])
        w_pool = list(df_stats[df_stats['標籤'] == "弱"]['號碼'])

        st.divider()
        st.subheader("🎯 基礎設定")
        star_mode = st.selectbox("玩法星數", options=list(range(1, 11)), index=2)
        
        # --- 校正機率排行榜 ---
        biases = []
        for s in range(star_mode + 1):
            for m in range(star_mode - s + 1):
                w = star_mode - s - m
                theo_ways = nCr(len(s_pool), s) * nCr(len(m_pool), m) * nCr(len(w_pool), w)
                if theo_ways == 0: continue
                actual_found = sum([nCr(len(set(d['號碼']).intersection(s_pool)), s) * nCr(len(set(d['號碼']).intersection(m_pool)), m) * nCr(len(set(d['號碼']).intersection(w_pool)), w) for d in data])
                bias_val = (actual_found / len(data)) / (theo_ways / nCr(80, star_mode) * 20)
                biases.append({"配比": f"{s}強{m}中{w}弱", "B": bias_val, "S": s, "M": m, "W": w})
        
        total_bias = sum([b['B'] for b in biases])
        if total_bias > 0:
            for b in biases: b['校正機率'] = (b['B'] / total_bias) * 100
        dist_df = pd.DataFrame(biases).sort_values("校正機率", ascending=False)
        
        st.write("📊 **配比信心排行榜 (校正)**")
        st.dataframe(dist_df[["配比", "校正機率"]].style.format({"校正機率": "{:.1f}%"}), hide_index=True)

# --- 4. 主畫面：功能分頁 ---
if st.session_state.full_data:
    t1, t2, t3 = st.tabs(["🚀 戰術選號", "📈 出現次數圖表", "📋 原始校驗"])

    with t1:
        # --- 選號比例與按鈕移至此處 ---
        st.markdown("### 🛠️ 組合配比配置器")
        c1, c2, c3 = st.columns(3)
        with c1: s_req = st.number_input("強勢號數量", 0, star_mode, int(dist_df.iloc[0]['S']))
        with c2: m_req = st.number_input("中性號數量", 0, star_mode - s_req, int(dist_df.iloc[0]['M']))
        with c3: w_req = star_mode - s_req - m_req
        
        st.info(f"當前策略：{star_mode}星玩法 ({s_req}強 / {m_req}中 / {w_req}弱)")
        
        if st.button("🎲 重新生成組合與歷史回測"):
            st.rerun()

        st.divider()
        st.subheader("📡 方案輸出與戰績")
        cols = st.columns(2)
        for i in range(4):
            p_s = random.sample(s_pool, min(len(s_pool), s_req)) if s_req > 0 else []
            p_m = random.sample(m_pool, min(len(m_pool), m_req)) if m_req > 0 else []
            p_w = random.sample(w_pool, min(len(w_pool), w_req)) if w_req > 0 else []
            final_set = sorted(p_s + p_m + p_w)
            
            # 回測邏輯
            hit_periods = [d['期數'] for d in data if set(final_set).issubset(set(d['號碼']))]
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="neon-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:0.8rem; color:#aaa;">OPTION #{i+1}</span>
                        <span class="ratio-tag">{len(p_s)}強 {len(p_m)}中 {len(p_w)}弱</span>
                    </div>
                    <div style="font-size:1.8rem; font-weight:900; letter-spacing:3px; color:#fff; margin:10px 0;">
                        {', '.join([f'{n:02d}' for n in final_set])}
                    </div>
                    <div class="history-hit">🏆 歷史全中：{len(hit_periods)} 次</div>
                    <div style="font-size:0.7rem; color:#00ffcc; margin-top:5px; height:40px; overflow-y:auto;">
                        {'期數: ' + ', '.join(hit_periods) if hit_periods else '※ 無中獎紀錄'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with t2:
        # 1. XY 軸出現次數圖
        st.subheader("📉 各號碼開出次數統計")
        fig = px.bar(df_stats, x='號碼', y='次數', color='標籤', 
                     color_discrete_map={"強": "#ff0055", "中": "#333", "弱": "#00ff88"},
                     labels={'次數': '出現總次數', '號碼': '球號'})
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # 2. 80 球機率矩陣
        st.subheader("📌 80球強中弱矩陣")
        grid_html = ""
        for n in range(1, 81):
            row = df_stats[df_stats['號碼'] == n].iloc[0]
            c = "highlight-s" if row['標籤'] == "強" else ("highlight-w" if row['標籤'] == "弱" else "")
            grid_html += f'<div class="ball-style {c}">{n:02d}</div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)

    with t3:
        st.subheader("📝 原始歷史數據全量清單")
        df_all = pd.DataFrame(st.session_state.full_data)
        df_all['號碼清單'] = df_all['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(df_all[['期數', '日期', '號碼清單']], use_container_width=True, height=600)

else:
    st.info("衛星連線中... 請先點擊左側「同步資料庫」開啟戰略控制台。")
