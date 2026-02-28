import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px
from datetime import datetime, timedelta

# --- 業界最強視覺配置：極致黑金 ---
st.set_page_config(page_title="BINGO 歷史數據終端", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #000; color: #ffcc00; }
    .stMetric { background: #111; border: 1px solid #ffcc00; border-radius: 10px; padding: 15px; }
    .recommend-box { 
        background: linear-gradient(135deg, #1a1a1a 0%, #333 100%); 
        border: 2px solid #ffcc00; color: #fff; padding: 20px; border-radius: 15px;
        box-shadow: 0 0 15px rgba(255, 204, 0, 0.3); margin: 15px 0;
    }
    .stButton>button { 
        background: linear-gradient(90deg, #ffcc00, #ff9900); color: black !important;
        font-weight: 900; border-radius: 50px; height: 3.5em; border: none; width: 100%;
    }
    .ball-style {
        display: inline-flex; width: 30px; height: 30px; background: #222;
        border: 1px solid #ffcc00; border-radius: 50%; justify-content: center;
        align-items: center; margin: 2px; font-size: 0.8rem; color: #ffcc00;
    }
    .super-ball { background: #ffcc00; color: #000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 歷史資料抓取核心 ---
def get_auzo_history_data(date_str):
    """抓取特定日期的奧索 BINGO 資料"""
    url = f"https://lotto.auzo.tw/bingobingo/list_{date_str}.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('tr.bingo_row')
        
        day_data = []
        for row in rows:
            period_el = row.select_one('td.BPeriod')
            if not period_el: continue
            
            period = period_el.find('b').text.strip()
            # 奧索的號碼在 tr 的第二個 td 內的所有 div
            ball_divs = row.find_all('td')[1].find_all('div')
            nums = []
            super_ball = None
            
            for d in ball_divs:
                val = d.text.strip()
                if val.isdigit():
                    n = int(val)
                    nums.append(n)
                    # 奧索超級獎號的 class 通常帶有 's'，例如 bbrps
                    cls = d.get('class', [''])[0]
                    if 's' in cls: super_ball = n
            
            if len(nums) >= 20:
                day_data.append({"期數": period, "號碼": sorted(nums), "超級獎號": super_ball, "日期": date_str})
        return day_data
    except:
        return []

# --- 主介面 ---
st.title("🛡️ BINGO 歷史數據監控終端")
st.markdown("##### 📍 奧索網實時解析版 | 安南區操盤手專用")

# 自動產生最近三天的日期
today = datetime.now()
dates = [(today - timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]

if 'raw_pool' not in st.session_state:
    st.session_state.raw_pool = []

# --- 步驟一：抓取前三天資料 ---
with st.container():
    st.subheader("📅 第一步：同步歷史資料庫")
    if st.button("🔄 立即同步最近三天歷史數據"):
        total_data = []
        progress_bar = st.progress(0)
        for idx, d in enumerate(dates):
            st.write(f"正在分析 {d}...")
            total_data.extend(get_auzo_history_data(d))
            progress_bar.progress((idx + 1) / 3)
        st.session_state.raw_pool = total_data
        st.success(f"同步完成！共取得 {len(total_data)} 筆開獎紀錄。")

# --- 步驟二：選擇筆數與分析 ---
if st.session_state.raw_pool:
    st.divider()
    st.subheader("📊 第二步：篩選筆數並執行強中弱分析")
    
    col_a, col_b = st.columns(2)
    with col_a:
        analysis_count = st.number_input("選擇最近幾筆進行分析", 10, len(st.session_state.raw_pool), 50)
    with col_b:
        star_mode = st.selectbox("玩法建議模式", ["三星", "四星", "五星"])

    # 取出使用者要的筆數
    target_data = st.session_state.raw_pool[:analysis_count]
    
    # 執行強中弱演算
    all_nums = [n for d in target_data for n in d['號碼']]
    counts = Counter(all_nums)
    for i in range(1, 81): counts.setdefault(i, 0)
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    S = [x[0] for x in sorted_items[:26]]
    M = [x[0] for x in sorted_items[26:52]]
    W = [x[0] for x in sorted_items[52:]]

    # 顯示強中弱面板
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 強勢區", f"{S[0]}, {S[1]}...")
    c2.metric("⚖️ 中性區", f"{M[0]}, {M[1]}...")
    c3.metric("❄️ 弱勢區", f"{W[0]}, {W[1]}...")

    # 組合建議
    st.markdown("### 🏆 AI 推薦投注組合")
    if star_mode == "三星":
        rec = f"{S[0]} (強), {S[1]} (強), {M[0]} (中)"
        tip = "策略：2強1中。熱門追蹤配上頻率穩定的中性號，機率最優。"
    elif star_mode == "四星":
        rec = f"{S[0]}, {S[1]}, {M[0]}, {M[1]}"
        tip = "策略：2強2中。平衡佈局，守住中間盤帶。"
    else:
        rec = f"{S[0]}, {S[1]}, {S[2]}, {M[0]}, {W[0]}"
        tip = "策略：3強1中1弱。博取冷門號碼回補的大獎。"

    st.markdown(f"""<div class="recommend-box">
        <h2 style='margin:0;'>{star_mode}建議：{rec}</h2>
        <p style='color:#aaa; margin-top:5px;'>{tip}</p>
    </div>""", unsafe_allow_html=True)

    # 每一筆號碼驗證 (你要的清單)
    with st.expander("🔍 原始號碼驗證清單 (已載入 {} 筆)".format(len(target_data))):
        for d in target_data:
            balls_html = "".join([f'<div class="ball-style {"super-ball" if n==d["超級獎號"] else ""}">{n:02d}</div>' for n in d['號碼']])
            st.markdown(f"**期數: {d['期數']}** ({d['日期']})<br>{balls_html}", unsafe_allow_html=True)

    # 圖表
    fig = px.bar(x=list(counts.keys()), y=list(counts.values()), labels={'x':'號碼', 'y':'次數'}, title="大數據出現頻率圖")
    fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("請點擊上方按鈕開始同步歷史數據。")

st.caption("數據來源：奧索樂透網歷史清單。分析結果僅供參考。")
