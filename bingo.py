import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- 1. 頂級賽博黑金 UI 配置 ---
st.set_page_config(page_title="BINGO 戰爭指揮中心", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 全域背景與發光字體 */
    [data-testid="stAppViewContainer"] { background: #000; color: #00ffcc; font-family: 'Consolas', monospace; }
    
    /* 霓虹卡片 */
    .neon-card { 
        background: rgba(10, 10, 20, 0.9); border: 2px solid #00ffcc; 
        border-radius: 12px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.4);
    }
    
    /* 推薦卡片加強版 */
    .recommend-box {
        background: linear-gradient(135deg, #121212 0%, #1e1e2f 100%);
        border: 2px solid #ff00ff; color: #fff; padding: 20px; border-radius: 10px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.3); border-left: 8px solid #ff00ff;
    }

    .stButton>button { 
        background: linear-gradient(45deg, #00ffcc, #0055ff); color: #000 !important;
        font-weight: 900; border-radius: 5px; height: 4em; border: 2px solid #fff;
        box-shadow: 0 5px 15px rgba(0, 255, 204, 0.4);
    }
    
    /* 球體動態視覺 */
    .ball-style {
        display: inline-flex; width: 34px; height: 34px; background: #000;
        border: 1px solid #00ffcc; border-radius: 5px; justify-content: center;
        align-items: center; margin: 3px; font-size: 0.95rem; font-weight: bold;
        box-shadow: inset 0 0 5px #00ffcc;
    }
    .super-ball { background: #ff00ff; border-color: #fff; color: #fff; box-shadow: 0 0 15px #ff00ff; }
    .miss-high { color: #ff0055; } /* 遺漏太久變紅色 */
    </style>
    """, unsafe_allow_html=True)

# --- 2. 強化版數據抓取系統 ---
@st.cache_data(ttl=300)
def fetch_multi_days(days=3):
    today = datetime.now()
    all_combined = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
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
                # 抓取開獎球與超級獎號
                ball_td = r.find_all('td')[1]
                divs = ball_td.find_all('div')
                nums = []
                super_n = None
                for d in divs:
                    v = d.text.strip()
                    if v.isdigit():
                        num = int(v)
                        nums.append(num)
                        if 's' in d.get('class', [''])[0]: super_n = num
                if len(nums) >= 20:
                    all_combined.append({"期數": p, "號碼": sorted(nums), "超級獎號": super_n, "日期": d_str})
        except: continue
    return all_combined

# --- 3. 核心運算：遺漏期數與機率 ---
def run_heavy_analysis(pool, sample):
    data = pool[:sample]
    counts = Counter([n for d in data for n in d['號碼']])
    super_counts = Counter([d['超級獎號'] for d in data if d['超級獎號']])
    
    stats = []
    latest_draw = data[0]['號碼']
    for i in range(1, 81):
        # 頻率
        freq = counts.get(i, 0) / len(data)
        # 遺漏 (幾期沒開)
        miss = 0
        for d in data:
            if i in d['號碼']: break
            miss += 1
        # 機率標籤 (25% +/- 5%)
        label = "🔥 強勢" if freq >= 0.30 else ("❄️ 弱勢" if freq <= 0.20 else "⚖️ 中性")
        stats.append({"號碼": i, "頻率": freq, "次數": counts.get(i, 0), "標籤": label, "遺漏": miss})
    
    return pd.DataFrame(stats), super_counts

# --- 4. UI 終端介面 ---
st.title("🌌 BINGO WAR-ROOM TERMINAL")
st.markdown("##### ⚡歷史數據三日鏈路同步")

if 'full_data' not in st.session_state: st.session_state.full_data = []

with st.sidebar:
    st.header("🛠️ 系統操作")
    if st.button("📡 同步三日資料庫"):
        st.session_state.full_data = fetch_multi_days(3)
    
    if st.session_state.full_data:
        st.success(f"目前載入: {len(st.session_state.full_data)} 期")
        sample_size = st.slider("分析深度(期)", 20, len(st.session_state.full_data), 100)
        st.divider()
        st.write("🔧 **選號比例配置**")
        s_req = st.number_input("幾強", 0, 10, 2)
        m_req = st.number_input("幾中", 0, 10, 1)
        w_req = st.number_input("幾弱", 0, 10, 0)

if st.session_state.full_data:
    df, s_counts = run_heavy_analysis(st.session_state.full_data, sample_size)
    s_pool = df[df['標籤'] == "🔥 強勢"]['號碼'].tolist()
    m_pool = df[df['標籤'] == "⚖️ 中性"]['號碼'].tolist()
    w_pool = df[df['標籤'] == "❄️ 弱勢"]['號碼'].tolist()

    # --- 頂部跑馬燈：當前 TOP 5 熱號 ---
    top5 = df.sort_values('頻率', ascending=False).head(5)['號碼'].tolist()
    st.warning(f"🚀 當前戰區最強熱號：{' · '.join([f'{n:02d}' for n in top5])}")

    tabs = st.tabs(["🎯 戰略輸出", "📈 深度矩陣", "🔮 超級獎號", "📋 原始校驗"])

    with tabs[0]:
        st.subheader("🚀 自定義比例生成方案")
        if st.button("🎲 重新運算選號邏輯"): st.rerun()
        
        cols = st.columns(2)
        for i in range(4):
            p_s = random.sample(s_pool, min(len(s_pool), s_req))
            p_m = random.sample(m_pool, min(len(m_pool), m_req))
            p_w = random.sample(w_pool, min(len(w_pool), w_req))
            final_set = sorted(p_s + p_m + p_w)
            with cols[i % 2]:
                st.markdown(f"""
                <div class="neon-card">
                    <div style="font-size:0.8rem; color:#00ffcc;">戰略組合 #{i+1} | {len(final_set)}星玩法</div>
                    <div style="font-size:2.2rem; font-weight:900; letter-spacing:5px;">{', '.join([f'{n:02d}' for n in final_set])}</div>
                    <div style="margin-top:10px; font-size:0.75rem; opacity:0.7;">比例：{s_req}強 / {m_req}中 / {w_req}弱</div>
                </div>
                """, unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("📈 80球數據健康報告")
        grid_html = ""
        for n in range(1, 81):
            row = df[df['號碼'] == n].iloc[0]
            c_style = "border-color:#ff0055; color:#ff0055;" if row['標籤'] == "🔥 強勢" else ("border-color:#00ff88; color:#00ff88;" if row['標籤'] == "❄️ 弱勢" else "")
            grid_html += f'<div class="ball-style" style="{c_style}">{n:02d}<br><small style="font-size:0.5rem; color:#555;">{row["遺漏"]}</small></div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)
        st.caption("球號下方數字為「遺漏期數」：數字越大代表越久沒開出。")

    with tabs[2]:
        st.subheader("🔮 超級獎號分佈圖 (分析深度期數)")
        s_df = pd.DataFrame(s_counts.items(), columns=['號碼', '次數']).sort_values('次數', ascending=False)
        fig_s = px.pie(s_df.head(10), values='次數', names='號碼', hole=.4, title="前10大超級獎號分佈")
        fig_s.update_layout(template="plotly_dark")
        st.plotly_chart(fig_s, use_container_width=True)

    with tabs[3]:
        st.subheader("📝 原始數據驗證（全量輸出）")
        st.write("以下為您篩選的期數完整清單：")
        
        # 顯示格式化表格
        display_df = pd.DataFrame(st.session_state.full_data[:sample_size])
        display_df['號碼'] = display_df['號碼'].apply(lambda x: ', '.join([f"{n:02d}" for n in x]))
        st.dataframe(display_df, use_container_width=True, height=500)
        
        csv = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載全量原始資料庫 (CSV)", csv, "bingo_full_data.csv", "text/csv")

else:
    st.info("🛰️ 系統待命。請在側邊欄點擊「同步最近三天資料庫」以開始作業。")

st.caption("🚨 機率僅供參考，強勢號不代表必開，請結合「遺漏期數」進行冷熱交叉選號。")
