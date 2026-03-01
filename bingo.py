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
st.set_page_config(page_title="BINGO 數據指揮中心 V8", layout="wide", initial_sidebar_state="expanded")

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

# --- 3. 側邊欄：期望值偏移分析 ---
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
        st.subheader("🎯 期望偏移分析")
        star_mode = st.selectbox("玩法星數", options=list(range(1, 11)), index=2)
        
        # --- 超強演算法：排除數量因子的偏移率 ---
        distribution = []
        total_drawn_combs = 0
        total_theoretical_combs = nCr(80, star_mode)
        
        # 計算每種配比在 80 球中「原本有多少組」 (數量因子)
        for s in range(star_mode + 1):
            for m in range(star_mode - s + 1):
                w = star_mode - s - m
                # 理論組數：從強球選s, 中球選m, 弱球選w
                theoretical_ways = nCr(len(s_pool), s) * nCr(len(m_pool), m) * nCr(len(w_pool), w)
                if theoretical_ways == 0: continue
                
                # 實際在歷史開獎中「出現了幾組」
                actual_found = 0
                for d in data:
                    draw_set = set(d['號碼'])
                    d_s = len([n for n in draw_set if n in s_pool])
                    d_m = len([n for n in draw_set if n in m_pool])
                    d_w = len([n for n in draw_set if n in w_pool])
                    actual_found += nCr(d_s, s) * nCr(d_m, m) * nCr(d_w, w)
                
                # 計算偏移率 = (實際組數/樣本期數) / (理論組數/理論總組數)
                # 這代表：相對於它的球數基數，這種組合是否更容易被開出
                theoretical_prob = theoretical_ways / total_theoretical_combs
                actual_avg_per_draw = actual_found / len(data)
                
                # 偏移倍率：大於 1 代表是真正的熱門組合
                bias = actual_avg_per_draw / (theoretical_prob * 20) # 修正係數
                
                distribution.append({
                    "配比": f"{s}強{m}中{w}弱",
                    "偏移倍率": bias,
                    "S": s, "M": m, "W": w
                })
        
        dist_df = pd.DataFrame(distribution).sort_values("偏移倍率", ascending=False)
        st.write("📈 **排除數量因子後的熱度排行榜**")
        st.dataframe(dist_df[["配比", "偏移倍率"]].style.format({"偏移倍率": "{:.2f}x"}), hide_index=True)
        st.caption("※ 倍率 > 1 代表該配比比理論上更容易開出。")

        st.divider()
        s_count = st.number_input("幾強", 0, star_mode, int(dist_df.iloc[0]['S']))
        m_count = st.number_input("幾中", 0, star_mode - s_count, int(dist_df.iloc[0]['M']))
        w_count = star_mode - s_count - m_count
        if st.button("🎲 重新生成組合與回測"): st.rerun()

# --- 4. 主畫面：數據看板 ---
if st.session_state.full_data:
    t1, t2, t3 = st.tabs(["🚀 戰術選號", "📈 出現統計", "📋 原始校驗"])
    with t1:
        cols = st.columns(2)
        for i in range(4):
            p_s = random.sample(s_pool, min(len(s_pool), s_count)) if s_count > 0 else []
            p_m = random.sample(m_pool, min(len(m_pool), m_count)) if m_count > 0 else []
            p_w = random.sample(w_pool, min(len(w_pool), w_count)) if w_count > 0 else []
            final_set = sorted(p_s + p_m + p_w)
            hit_periods = [d['期數'] for d in data if set(final_set).issubset(set(d['號碼']))]
            with cols[i % 2]:
                st.markdown(f"""<div class="neon-card">
                    <div style="font-size:1.8rem; font-weight:900; color:#fff;">{', '.join([f'{n:02d}' for n in final_set])}</div>
                    <div class="history-hit">🏆 歷史全中：{len(hit_periods)} 次</div>
                    <div style="font-size:0.7rem; color:#00ffcc; height:40px; overflow-y:auto;">{'期數: '+', '.join(hit_periods) if hit_periods else '※ 無中獎紀錄'}</div>
                </div>""", unsafe_allow_html=True)
    with t2:
        fig = px.bar(df_stats, x='號碼', y='次數', color='標籤', color_discrete_map={"強": "#ff0055", "中": "#333", "弱": "#00ff88"})
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with t3:
        display_df = pd.DataFrame(st.session_state.full_data)
        display_df['號碼'] = display_df['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(display_df[['期數', '日期', '號碼']], use_container_width=True, height=600)
else:
    st.info("請先點擊側邊欄「同步資料庫」。")
