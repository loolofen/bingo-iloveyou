import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px
from datetime import datetime, timedelta
import random

# --- 1. 業界最強黑金 UI：極速響應設計 ---
st.set_page_config(page_title="BINGO 自由配賦戰略終端", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #020205; color: #00d4ff; font-family: 'Consolas', monospace; }
    .stMetric { background: rgba(0, 212, 255, 0.05); border: 1px solid #00d4ff; border-radius: 8px; padding: 10px; }
    
    /* 專業戰術卡片 */
    .recommend-card { 
        background: linear-gradient(145deg, #0a0a1a 0%, #151525 100%); 
        border: 1px solid #00d4ff; color: #fff; padding: 20px; border-radius: 8px;
        margin-bottom: 15px; border-top: 4px solid #00d4ff;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
    }
    .tag-container { margin-bottom: 12px; display: flex; gap: 8px; align-items: center;}
    .tag { padding: 4px 10px; border-radius: 3px; font-size: 0.75rem; font-weight: 800; }
    .tag-s { background: #ff0055; color: white; box-shadow: 0 0 10px #ff0055aa; } 
    .tag-m { background: #222; color: #00d4ff; border: 1px solid #00d4ff; } 
    .tag-w { background: #00ff88; color: #000; box-shadow: 0 0 10px #00ff88aa; }

    .stButton>button { 
        background: #00d4ff; color: #000 !important; font-weight: 900;
        border-radius: 2px; height: 3.5em; border: none; width: 100%;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { background: #fff; box-shadow: 0 0 25px #00d4ff; }
    
    .ball-box {
        display: inline-flex; width: 32px; height: 32px; background: #000;
        border: 1px solid #333; border-radius: 2px; justify-content: center;
        align-items: center; margin: 2px; font-size: 0.9rem; font-weight: bold;
    }
    .strong-ball { border-color: #ff0055; color: #ff0055; }
    .weak-ball { border-color: #00ff88; color: #00ff88; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 高速數據抓取核心 ---
@st.cache_data(ttl=300)
def fetch_history(date_str):
    url = f"https://lotto.auzo.tw/bingobingo/list_{date_str}.html"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('tr.bingo_row')
        return [{"期數": r.select_one('td.BPeriod').find('b').text.strip(), 
                 "號碼": [int(d.text) for d in r.find_all('td')[1].find_all('div') if d.text.isdigit()]} 
                for r in rows if r.select_one('td.BPeriod')]
    except: return []

# --- 3. 狀態初始化 ---
if 'pool' not in st.session_state: st.session_state.pool = []

# --- UI 佈局 ---
st.title("🛰️ BINGO CUSTOM-STRATEGY X1")
st.markdown("##### 📍 安南區數據分析中心 · 自定義機率配賦版本")

# 數據源控制區
with st.sidebar:
    st.header("📡 數據鏈路系統")
    if st.button("🔄 同步最近三天開獎紀錄"):
        today = datetime.now()
        all_d = []
        for i in range(3):
            all_d.extend(fetch_history((today - timedelta(days=i)).strftime('%Y%m%d')))
        st.session_state.pool = all_d
    
    if st.session_state.pool:
        st.write(f"當前資料庫：{len(st.session_state.pool)} 期")
        sample = st.slider("樣本深度", 30, len(st.session_state.pool), 100)

if st.session_state.pool:
    # 頻率計算
    work_data = st.session_state.pool[:sample]
    counts = Counter([n for d in work_data for n in d['號碼']])
    df = pd.DataFrame([{"號碼": i, "頻率": counts.get(i, 0)/len(work_data)} for i in range(1, 81)])
    
    # 機率位移切分 (基線 25%)
    s_pool = df[df['頻率'] >= 0.30]['號碼'].tolist() # 強勢 > 30%
    w_pool = df[df['頻率'] <= 0.20]['號碼'].tolist() # 弱勢 < 20%
    m_pool = df[(df['頻率'] > 0.20) & (df['頻率'] < 0.30)]['號碼'].tolist() # 中性

    # --- 核心操作區 ---
    st.divider()
    t1, t2, t3 = st.tabs(["🎯 戰略生成", "📊 分佈矩陣", "📝 原始校驗"])

    with t1:
        st.markdown("### 🛠️ 自定義組合配置器")
        c1, c2, c3 = st.columns(3)
        with c1: s_req = st.number_input("強勢號數量", 0, 10, 2)
        with c2: m_req = st.number_input("中性號數量", 0, 10, 1)
        with c3: w_req = st.number_input("弱勢號數量", 0, 10, 0)
        
        total_balls = s_req + m_req + w_req
        st.write(f"🔍 目前選號玩法：**{total_balls} 星組合**")
        
        if st.button("🎲 依此比例重新生成 4 組方案"):
            st.rerun()

        st.subheader("🚀 戰術方案輸出")
        cols = st.columns(2)
        
        for i in range(4):
            # 防呆：確保池子夠抽
            p_s = random.sample(s_pool, min(len(s_pool), s_req))
            p_m = random.sample(m_pool, min(len(m_pool), m_req))
            p_w = random.sample(w_pool, min(len(w_pool), w_req))
            
            final_set = sorted(p_s + p_m + p_w)
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="recommend-card">
                    <div class="tag-container">
                        <span class="tag tag-s">{len(p_s)}強</span>
                        <span class="tag tag-m">{len(p_m)}中</span>
                        <span class="tag tag-w">{len(p_w)}弱</span>
                        <span style="margin-left:auto; color:#444;">#{i+1}</span>
                    </div>
                    <div style="font-size:2rem; letter-spacing:5px; font-weight:900; color:#fff; text-shadow: 0 0 10px #00d4ff;">
                        {', '.join([f'{n:02d}' for n in final_set])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with t2:
        st.subheader("📈 機率偏移熱圖")
        st.markdown("<p style='color:#888;'>🔴 強勢(>30%) | ⚪ 中性 | 🟢 弱勢(<20%)</p>", unsafe_allow_html=True)
        
        grid_html = ""
        for n in range(1, 81):
            f = counts.get(n, 0)/len(work_data)
            c = "strong-ball" if f >= 0.30 else ("weak-ball" if f <= 0.20 else "")
            grid_html += f'<div class="ball-box {c}">{n:02d}</div>'
            if n % 10 == 0: grid_html += "<br>"
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # 視覺化圖表
        df['標籤'] = df['頻率'].apply(lambda x: '強' if x >= 0.30 else ('弱' if x <= 0.20 else '中'))
        fig = px.bar(df, x='號碼', y='頻率', color='標籤', 
                     color_discrete_map={'強': '#ff0055', '中': '#333', '弱': '#00ff88'})
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with t3:
        st.subheader("🔍 歷史樣本驗證")
        df_view = pd.DataFrame(work_data)
        df_view['號碼'] = df_view['號碼'].apply(lambda x: sorted(x))
        st.table(df_view.head(20))

else:
    st.warning("⚠️ 請先在左側選單點擊「同步最近三天數據庫」以開啟分析功能。")

st.caption("系統警告：此工具僅供安南區戰略研究使用。數據同步自奧索歷史清單。")
