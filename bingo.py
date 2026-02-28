import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px
from datetime import datetime, timedelta
import random

# --- 1. 賽博黑金 UI 配置 ---
st.set_page_config(page_title="BINGO 戰略指揮中心 V3", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #000; color: #00ffcc; font-family: 'Consolas', monospace; }
    .neon-card { 
        background: rgba(10, 10, 20, 0.9); border: 2px solid #00ffcc; 
        border-radius: 10px; padding: 20px; margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
    }
    .stButton>button { 
        background: #00ffcc; color: #000 !important; font-weight: 900;
        border-radius: 4px; height: 3.5em; width: 100%; border: none;
    }
    .ball-style {
        display: inline-flex; width: 35px; height: 35px; background: #111;
        border: 1px solid #444; border-radius: 5px; justify-content: center;
        align-items: center; margin: 2px; font-size: 0.9rem; font-weight: bold;
    }
    .highlight-s { border-color: #ff0055; color: #ff0055; box-shadow: 0 0 8px #ff0055aa; }
    .highlight-w { border-color: #00ff88; color: #00ff88; box-shadow: 0 0 8px #00ff88aa; }
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

# --- 3. 初始化 ---
if 'full_data' not in st.session_state: st.session_state.full_data = []

with st.sidebar:
    st.header("🛰️ 系統控制台")
    if st.button("🔄 同步最近三日資料庫"):
        st.session_state.full_data = fetch_bingo_data(3)
    
    if st.session_state.full_data:
        st.success(f"已同步 {len(st.session_state.full_data)} 期")
        sample_size = st.slider("分析深度 (期)", 30, len(st.session_state.full_data), 100)
        st.divider()
        
        # --- 玩法鎖定邏輯 ---
        st.subheader("🎯 玩法配比設定")
        star_mode = st.selectbox("選擇星數玩法", options=list(range(1, 11)), index=4) # 預設五星
        
        s_count = st.number_input("強勢號數量", 0, star_mode, 2)
        remaining = star_mode - s_count
        m_count = st.number_input("中性號數量", 0, remaining, min(remaining, 2))
        w_count = star_mode - s_count - m_count
        
        st.info(f"當前配置：{star_mode}星\n({s_count}強 + {m_count}中 + {w_count}弱)")
        
        if (s_count + m_count + w_count) != star_mode:
            st.error("❌ 配比加總不等於星數！")

if st.session_state.full_data:
    # 運算頻率
    data = st.session_state.full_data[:sample_size]
    all_nums = [n for d in data for n in d['號碼']]
    counts = Counter(all_nums)
    
    stats = []
    for i in range(1, 81):
        freq = counts.get(i, 0) / len(data)
        label = "🔥 強" if freq >= 0.30 else ("❄️ 弱" if freq <= 0.20 else "⚖️ 中")
        stats.append({"號碼": i, "頻率": freq, "標籤": label})
    
    df = pd.DataFrame(stats)
    s_pool = df[df['標籤'] == "🔥 強"]['號碼'].tolist()
    m_pool = df[df['標籤'] == "⚖️ 中"]['號碼'].tolist()
    w_pool = df[df['標籤'] == "❄️ 弱"]['號碼'].tolist()

    tabs = st.tabs(["🎯 戰略選號", "📈 機率矩陣", "📋 原始校驗"])

    with tabs[0]:
        st.subheader(f"🚀 {star_mode}星方案：{s_count}強 / {m_count}中 / {w_count}弱")
        if st.button("🎲 重新生成組合"): st.rerun()
        
        cols = st.columns(2)
        for i in range(4):
            # 抽樣邏輯
            p_s = random.sample(s_pool, min(len(s_pool), s_count))
            p_m = random.sample(m_pool, min(len(m_pool), m_count))
            p_w = random.sample(w_pool, min(len(w_pool), w_count))
            final_set = sorted(p_s + p_m + p_w)
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="neon-card">
                    <div style="font-size:0.8rem; color:#aaa;">RANK {i+1} OPTION</div>
                    <div style="font-size:2rem; font-weight:900; letter-spacing:3px; color:#fff;">
                        {', '.join([f'{n:02d}' for n in final_set])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("📊 80球全機率分佈")
        grid_html = ""
        for n in range(1, 81):
            row = df[df['號碼'] == n].iloc[0]
            c = "highlight-s" if row['標籤'] == "🔥 強" else ("highlight-w" if row['標籤'] == "❄️ 弱" else "")
            grid_html += f'<div class="ball-style {c}">{n:02d}</div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)
        
        fig = px.bar(df, x='號碼', y='頻率', color='標籤', color_discrete_map={"🔥 強": "#ff0055", "⚖️ 中": "#444", "❄️ 弱": "#00ff88"})
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("📝 原始歷史數據核對清單")
        # 直接顯示全部號碼，方便核對
        display_df = pd.DataFrame(st.session_state.full_data)
        display_df['號碼清單'] = display_df['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(display_df[['期數', '日期', '號碼清單']], use_container_width=True, height=600)
        
        csv = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載完整 CSV 資料庫", csv, "bingo_history.csv", "text/csv")

else:
    st.info("請先點擊側邊欄「同步最近三日資料庫」啟動系統。")
