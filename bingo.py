import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
import random
import math

# --- 1. 賽博黑金 UI 配置 ---
st.set_page_config(page_title="BINGO 數據指揮中心 Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #000; color: #00ffcc; font-family: 'Consolas', monospace; }
    [data-testid="stSidebar"] { background-color: #050510; border-right: 1px solid #00ffcc; }
    
    /* 霓虹卡片 */
    .neon-card { 
        background: rgba(10, 10, 20, 0.9); border: 1px solid #00ffcc; 
        border-radius: 10px; padding: 20px; margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
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
    
    .history-hit { color: #ff00ff; font-size: 0.85rem; font-weight: bold; margin-top: 10px; }
    .ratio-tag { background: #333; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; color: #00ffcc; border: 1px solid #00ffcc; }
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

# --- 3. 側邊欄邏輯 (重新排序) ---
if 'full_data' not in st.session_state: st.session_state.full_data = []

with st.sidebar:
    st.header("🛰️ 系統控制台")
    if st.button("🔄 同步最近三日資料庫"):
        st.session_state.full_data = fetch_bingo_data(3)
    
    if st.session_state.full_data:
        st.success(f"已同步 {len(st.session_state.full_data)} 期")
        sample_size = st.slider("分析深度 (期)", 30, len(st.session_state.full_data), 100)
        
        data = st.session_state.full_data[:sample_size]
        all_nums = [n for d in data for n in d['號碼']]
        counts = Counter(all_nums)
        stats = []
        for i in range(1, 81):
            freq = counts.get(i, 0) / len(data)
            label = "強" if freq >= 0.30 else ("弱" if freq <= 0.20 else "中")
            stats.append({"號碼": i, "標籤": label})
        df_stats = pd.DataFrame(stats)
        s_pool = set(df_stats[df_stats['標籤'] == "強"]['號碼'])
        m_pool = set(df_stats[df_stats['標籤'] == "中"]['號碼'])
        w_pool = set(df_stats[df_stats['標籤'] == "弱"]['號碼'])

        st.divider()
        st.subheader("🎯 玩法配比設定")
        star_mode = st.selectbox("選擇星數玩法", options=list(range(1, 11)), index=2)
        
        # --- 組合分佈排行榜 (移至上方) ---
        st.write("📊 **歷史配比機率排行**")
        distribution = Counter()
        total_combs = 0
        for d in data:
            draw_set = set(d['號碼'])
            d_s, d_m, d_w = len(draw_set.intersection(s_pool)), len(draw_set.intersection(m_pool)), len(draw_set.intersection(w_pool))
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

        st.divider()
        # 自選輸入
        s_count = st.number_input("自選：幾強", 0, star_mode, 2)
        remaining = star_mode - s_count
        m_count = st.number_input("自選：幾中", 0, remaining, min(remaining, 1))
        w_count = star_mode - s_count - m_count
        st.info(f"當前配置：{s_count}強 {m_count}中 {w_count}弱")

# --- 4. 主畫面邏輯 ---
if st.session_state.full_data:
    tabs = st.tabs(["🎯 戰略選號", "📈 機率矩陣", "📋 原始校驗"])

    with tabs[0]:
        st.subheader(f"🚀 {star_mode}星方案：歷史命中回測")
        if st.button("🎲 重新生成組合並回測"): st.rerun()
        
        cols = st.columns(2)
        for i in range(4):
            # 隨機抽樣產生組合
            p_s = random.sample(list(s_pool), min(len(s_pool), s_count))
            p_m = random.sample(list(m_pool), min(len(m_pool), m_count))
            p_w = random.sample(list(w_pool), min(len(w_pool), w_count))
            final_set = sorted(p_s + p_m + p_w)
            
            # 回測
            hit_periods = [d['期數'] for d in data if set(final_set).issubset(set(d['號碼']))]
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="neon-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:0.8rem; color:#aaa;">RANK {i+1} OPTION</span>
                        <span class="ratio-tag">{len(p_s)}強 {len(p_m)}中 {len(p_w)}弱</span>
                    </div>
                    <div style="font-size:2rem; font-weight:900; letter-spacing:3px; color:#fff; margin:10px 0;">
                        {', '.join([f'{n:02d}' for n in final_set])}
                    </div>
                    <div class="history-hit">🏆 歷史全中：{len(hit_periods)} 次</div>
                    <div style="font-size:0.75rem; color:#00ffcc; margin-top:5px; word-wrap: break-word;">
                        {'期數: ' + ', '.join(hit_periods) if hit_periods else '※ 樣本內無全中紀錄'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("📊 80球全機率分佈")
        st.markdown("<p style='color:#888;'>🔴: 強勢(>30%) | ⚪: 中性 | 🟢: 弱勢(<20%)</p>", unsafe_allow_html=True)
        grid_html = ""
        for n in range(1, 81):
            row = df_stats[df_stats['號碼'] == n].iloc[0]
            c = "highlight-s" if row['標籤'] == "強" else ("highlight-w" if row['標籤'] == "弱" else "")
            grid_html += f'<div class="ball-style {c}">{n:02d}</div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("📝 原始歷史數據核對清單")
        # 直接秀出全部號碼，包含超級獎號解析
        display_df = pd.DataFrame(st.session_state.full_data)
        display_df['號碼清單'] = display_df['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(display_df[['期數', '日期', '號碼清單']], use_container_width=True, height=600)

else:
    st.info("請先點擊側邊欄「同步最近三日資料庫」啟動系統。")
