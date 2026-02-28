import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import plotly.express as px

# --- 業界最強視覺：霓虹黑金 UI ---
st.set_page_config(page_title="BINGO 終極操盤手", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0a0a0a; color: #ffca28; }
    .stMetric { background: #1a1a1a; border: 1px solid #ffca28; border-radius: 15px; box-shadow: 0 0 10px #ffca2844; }
    .recommend-card { 
        background: linear-gradient(135deg, #222, #333); border-left: 8px solid #ffca28;
        padding: 20px; border-radius: 10px; color: #fff; margin: 20px 0;
    }
    .stButton>button { 
        background: linear-gradient(90deg, #ffca28, #ffd54f); color: black !important;
        font-weight: 900; border-radius: 50px; height: 3.5em; border: none;
    }
    .ball-circle {
        display: inline-flex; width: 32px; height: 32px; background: #222;
        border: 1px solid #ffca28; border-radius: 50%; justify-content: center;
        align-items: center; margin: 3px; font-size: 0.9rem; color: #ffca28;
    }
    .super-ball { background: #ffca28; color: #000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 爬蟲核心：模擬瀏覽器解析 HTML ---
def get_bingo_stable_data(target_periods):
    # 這是你提供給我的歷史網址
    url = "https://www.taiwanlottery.com.tw/lotto/result/bingo_bingo"
    
    # 關鍵：模擬真實瀏覽器，避免被伺服器封鎖
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.taiwanlottery.com.tw/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 強制編碼避免亂碼
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 根據你提供的 HTML 結構定位
        items = soup.select('.result-item')
        extracted = []
        
        for item in items:
            # 抓取期數
            period_el = item.select_one('.period-title')
            period = period_el.text.strip().replace("第", "").replace("期", "") if period_el else "Unknown"
            
            # 抓取所有球號
            ball_container = item.select_one('.result-item-simple-area-ball-container')
            if ball_container:
                balls = ball_container.select('.ball')
                # 排除非數字內容 (例如 "-" )
                nums = [int(b.text.strip()) for b in balls if b.text.strip().isdigit()]
                
                # 識別超級獎號 (類別包含 color-super)
                super_ball_el = ball_container.select_one('.color-super')
                super_val = int(super_ball_el.text.strip()) if super_ball_el else None
                
                if len(nums) >= 20:
                    extracted.append({
                        "期數": period,
                        "號碼": sorted(nums),
                        "超級獎號": super_val
                    })
        
        return extracted[:target_periods]

    except Exception as e:
        st.error(f"連線或解析失敗。建議：若上架後報錯，可能是台彩防火牆阻擋伺服器 IP。")
        return []

# --- 核心邏輯：強中弱分析 ---
def calculate_groups(data):
    all_n = []
    for d in data: all_n.extend(d['號碼'])
    counts = Counter(all_n)
    for i in range(1, 81): counts.setdefault(i, 0)
    
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    # 26/26/28 切分
    strong = [x[0] for x in sorted_items[:26]]
    medium = [x[0] for x in sorted_items[26:52]]
    weak = [x[0] for x in sorted_items[52:]]
    return strong, medium, weak, counts

# --- APP 介面 ---
st.markdown("<h1 style='text-align: center;'>🔱 BINGO PRO 實戰終端</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>安南區操盤專用 · 官網數據同步解析</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🎛️ 參數控管")
    num_p = st.slider("分析期數深度", 5, 50, 20)
    star_type = st.selectbox("目標組合玩法", ["三星", "四星", "五星"])

if st.button("🏁 開始抓取並計算強中弱"):
    with st.spinner("正在穿越防火牆讀取官網資料..."):
        real_data = get_bingo_stable_data(num_p)
    
    if real_data:
        S, M, W, full_counts = calculate_groups(real_data)
        
        # 1. 強中弱面板
        col1, col2, col3 = st.columns(3)
        col1.metric("🔥 強勢熱碼", f"{S[0]}, {S[1]}")
        col2.metric("⚖️ 中性溫碼", f"{M[0]}, {M[1]}")
        col3.metric("❄️ 冷門冰碼", f"{W[0]}, {W[1]}")

        # 2. 選號策略建議
        st.subheader("🎯 智能推薦組合")
        if star_type == "三星":
            comb = f"{S[0]}, {S[1]}, {M[0]}"
            strat = "【2強 + 1中】組合：熱門追蹤配上頻率穩定的中性號，機率最優。"
        elif star_type == "四星":
            comb = f"{S[0]}, {S[1]}, {M[0]}, {M[1]}"
            strat = "【2強 + 2中】組合：避開極端冷門，守住中間盤帶。"
        else:
            comb = f"{S[0]}, {S[1]}, {S[2]}, {M[0]}, {W[0]}"
            strat = "【3強 + 1中 + 1弱】組合：三強穩住勝率，一弱博取冷門加倍。"
            
        st.markdown(f"""<div class="recommend-card">
            <h3>{star_type}建議號碼：{comb}</h3>
            <p style='font-size: 0.9rem; opacity: 0.8;'>{strat}</p>
        </div>""", unsafe_allow_html=True)

        # 3. 真實數據驗證 (這就是你要的核對)
        with st.expander("🔍 官方原始號碼核對清單"):
            for d in real_data:
                balls_html = "".join([f'<div class="ball-circle {"super-ball" if n == d["超級獎號"] else ""}">{n:02d}</div>' for n in d['號碼']])
                st.markdown(f"**第 {d['期數']} 期**<br>{balls_html}", unsafe_allow_html=True)

        # 4. 統計分析圖表
        st.subheader("📊 近期號碼出現頻率 (1-80)")
        df_plot = pd.DataFrame(full_counts.items(), columns=['號碼', '頻率']).sort_values('號碼')
        fig = px.bar(df_plot, x='號碼', y='頻率', color='頻率', color_continuous_scale='YlOrRd')
        fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ 官網回應異常或目前無資料（通常是因為台彩網站點進去後需要按下查詢）。")
        st.info("💡 解決方案：若部署至 Cloud 遇到 IP 封鎖，建議使用此 App 於本地端運行 (streamlit run app.py)，效果最穩。")

st.caption("數據僅供分析參考，博弈必有風險。")
