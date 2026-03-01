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
st.set_page_config(page_title="BINGO 數據指揮中心 V7", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #000; color: #00ffcc; font-family: 'Consolas', monospace; }
    [data-testid="stSidebar"] { background-color: #050510; border-right: 1px solid #00ffcc; }
    
    .neon-card { 
        background: rgba(10, 10, 20, 0.9); border: 1px solid #00ffcc; 
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
    }
    
    .stButton>button { 
        background: #00ffcc; color: #000 !important; font-weight: 900;
        border-radius: 4px; height: 3.5em; width: 100%; border: none;
    }
    
    .ball-style {
        display: inline-flex; width: 32px; height: 32px; background: #111;
        border: 1px solid #444; border-radius: 5px; justify-content: center;
        align-items: center; margin: 2px; font-size: 0.85rem; font-weight: bold;
    }
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
                if len(nums) >= 20:
                    results.append({"期數": p, "號碼": sorted(nums), "日期": d_str})
        except: continue
    return results

def nCr(n, r):
    if r < 0 or r > n: return 0
    return math.comb(n, r)

# --- 3. 側邊欄：完整操作鏈 ---
if 'full_data' not in st.session_state: st.session_state.full_data = []

with st.sidebar:
    st.header("🛰️ 系統控制台")
    if st.button("🔄 同步最近三日資料庫"):
        st.session_state.full_data = fetch_bingo_data(3)
    
    if st.session_state.full_data:
        st.success(f"已同步 {len(st.session_state.full_data)} 期")
        sample_size = st.slider("分析深度 (期)", 30, len(st.session_state.full_data), 100)
        
        # 預計算強中弱池
        data = st.session_state.full_data[:sample_size]
        counts = Counter([n for d in data for n in d['號碼']])
        df_stats = pd.DataFrame([{"號碼": i, "頻率": counts.get(i, 0)/len(data), "次數": counts.get(i, 0)} for i in range(1, 81)])
        df_stats['標籤'] = df_stats['頻率'].apply(lambda x: "強" if x >= 0.30 else ("弱" if x <= 0.20 else "中"))
        
        s_pool = list(df_stats[df_stats['標籤'] == "強"]['號碼'])
        m_pool = list(df_stats[df_stats['標籤'] == "中"]['號碼'])
        w_pool = list(df_stats[df_stats['標籤'] == "弱"]['號碼'])

        st.divider()
        st.subheader("🎯 玩法配比設定")
        star_mode = st.selectbox("玩法星數", options=list(range(1, 11)), index=2)
        
        # 自選號碼區域 (緊接玩法設定)
        s_count = st.number_input("幾強", 0, star_mode, min(len(s_pool), 2))
        remaining = star_mode - s_count
        m_count = st.number_input("幾中", 0, remaining, min(len(m_pool), remaining))
        w_count = star_mode - s_count - m_count
        st.info(f"當前配比：{s_count}強 {m_count}中 {w_count}弱")

        # 重新選號按鈕也放在左邊，方便手機操作
        if st.button("🎲 重新生成組合與回測"):
            st.rerun()

        st.divider()
        st.write("📊 **全域配比機率參考**")
        distribution = Counter()
        total_combs = 0
        for d in data:
            draw_set = set(d['號碼'])
            d_s = len([n for n in draw_set if n in s_pool])
            d_m = len([n for n in draw_set if n in m_pool])
            d_w = len([n for n in draw_set if n in w_pool])
            for s in range(star_mode + 1):
                for m in range(star_mode - s + 1):
                    w = star_mode - s - m
                    combs = nCr(d_s, s) * nCr(d_m, m) * nCr(d_w, w)
                    if combs > 0:
                        distribution[f"{s}強{m}中{w}弱"] += combs
                        total_combs += combs
        
        if total_combs > 0:
            dist_list = [{"配比": k, "機率": (v/total_combs)*100} for k, v in distribution.items()]
            dist_df = pd.DataFrame(dist_list).sort_values("機率", ascending=False)
            st.dataframe(dist_df.style.format({"機率": "{:.2f}%"}), hide_index=True)

# --- 4. 主畫面：數據看板 ---
if st.session_state.full_data:
    t1, t2, t3 = st.tabs(["🚀 戰術選號輸出", "📈 出現次數圖表", "📋 原始校驗"])

    with t1:
        st.subheader(f"戰略方案 ({star_mode}星)")
        cols = st.columns(2)
        for i in range(4):
            # 隨機抽樣
            p_s = random.sample(s_pool, min(len(s_pool), s_count)) if s_count > 0 else []
            p_m = random.sample(m_pool, min(len(m_pool), m_count)) if m_count > 0 else []
            p_w = random.sample(w_pool, min(len(w_pool), w_count)) if w_count > 0 else []
            final_set = sorted(p_s + p_m + p_w)
            
            # 回測
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
                        {'期數: ' + ', '.join(hit_periods) if hit_periods else '※ 樣本內無全中紀錄'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with t2:
        # 1. XY 軸出現次數圖 (X=號碼, Y=次數)
        st.subheader("📉 歷史獎號出現次數統計 (XY 軸分析)")
        fig = px.bar(df_stats, x='號碼', y='次數', color='標籤', 
                     title=f"最近 {sample_size} 期各號碼開出總次數",
                     color_discrete_map={"強": "#ff0055", "中": "#333", "弱": "#00ff88"},
                     labels={'次數': '開出次數', '號碼': '球號'})
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # 2. 80 球機率矩陣
        st.subheader("📌 80球機率矩陣看板")
        grid_html = ""
        for n in range(1, 81):
            row = df_stats[df_stats['號碼'] == n].iloc[0]
            c = "highlight-s" if row['標籤'] == "強" else ("highlight-w" if row['標籤'] == "弱" else "")
            grid_html += f'<div class="ball-style {c}">{n:02d}</div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)

    with t3:
        st.subheader("📝 原始歷史全量數據清單")
        # 顯示全部資料，包含期數、日期、所有開出的 20 顆球
        df_all = pd.DataFrame(st.session_state.full_data)
        df_all['號碼清單'] = df_all['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(df_all[['期數', '日期', '號碼清單']], use_container_width=True, height=700)

else:
    st.info("🛰️ 系統待命中。請先在左側點擊「同步資料庫」開啟戰情室。")
