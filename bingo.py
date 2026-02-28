import streamlit as st
import pandas as pd
import requests
import random
import collections

# --- 網頁配置：完美適配手機 ---
st.set_page_config(page_title="BINGO 數據大師", layout="centered")

st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 1rem; }
    .stMetric { background: #f0f2f6; padding: 10px; border-radius: 10px; }
    button[kind="primary"] { background-color: #ff4b4b; border-color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心抓取：模擬 AUZO 數據源 ---
def get_bingo_data(count=20):
    # 使用其資料來源的 URL (模擬瀏覽器 header 避開阻擋)
    url = "https://lotto.auzo.tw/bingobingo.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": "https://lotto.auzo.tw/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 由於該站是 PHP 動態渲染，我們直接抓取其 Table 結構並轉為 Dataframe
        # 這是目前最穩定的「抄用法」方式
        dfs = pd.read_html(response.text)
        df = dfs[0] # 通常第一個表格就是資料
        
        # 整理資料列
        df.columns = ['期別', '開獎號碼', '超級獎號', '猜大小']
        df = df.head(count)
        
        # 將開獎號碼字串轉為數字列表
        df['號碼列表'] = df['開獎號碼'].apply(lambda x: [int(i) for i in str(x).split(',') if i.isdigit()])
        return df
    except Exception as e:
        st.error(f"數據連線失敗: {e}")
        return pd.DataFrame()

# --- 主畫面 ---
st.title("🎰 BINGO 智慧分析儀")
st.caption("同步 AUZO 即時數據 | 業界機率分析模式")

# 側邊欄設定
num_p = st.sidebar.slider("分析期數", 10, 50, 20)
game_star = st.sidebar.radio("目標玩法", ["三星", "四星", "五星"])

if st.button("🚀 獲取最新強中弱組合", type="primary", use_container_width=True):
    with st.spinner('正在分析數據規律...'):
        df = get_bingo_data(num_p)
        
        if not df.empty:
            # 1. 統計 1-80 號頻率
            all_n = [n for sublist in df['號碼列表'] for n in sublist]
            counts = collections.Counter(all_n)
            
            # 2. 強中弱機率切割 (業界三分法)
            # 排序：出現次數多到少
            sorted_freq = sorted(range(1, 81), key=lambda x: counts[x], reverse=True)
            strong = sorted_freq[:20]  # 前 25% 為強
            weak = sorted_freq[-20:]    # 後 25% 為弱
            middle = [i for i in range(1, 81) if i not in strong and i not in weak]

            # 3. 顯示即時狀態 (手機卡片)
            st.success(f"✅ 已抓取最新期：{df.iloc[0]['期別']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔴 強勢熱號", f"{len(strong)}個", "Hot")
            col2.metric("🟡 中間平衡", f"{len(middle)}個", "Mid")
            col3.metric("🟢 弱勢冷號", f"{len(weak)}個", "Cold")

            st.divider()

            # 4. 針對不同星等的建議組合 (核心邏輯)
            st.subheader(f"💡 {game_star} 組合建議")
            
            def suggest(star, s, m, w):
                # 業界最高機率策略：2強+1中 或 2強+1中+1弱
                s_pick = random.sample(s, 2 if star != "五星" else 3)
                m_pick = random.sample(m, 1)
                w_pick = random.sample(w, 1)
                
                if star == "三星":
                    return f"建議：**2強 + 1中**\n推薦號碼：`{sorted(s_pick + m_pick)}`"
                elif star == "四星":
                    return f"建議：**2強 + 1中 + 1弱**\n推薦號碼：`{sorted(s_pick + m_pick + w_pick)}`"
                else: # 五星
                    return f"建議：**3強 + 1中 + 1弱**\n推薦號碼：`{sorted(s_pick + m_pick + w_pick)}`"

            st.info(suggest(game_star, strong, middle, weak))
            
            # 5. 強勢號碼明細
            with st.expander("查看當前強勢號碼清單"):
                st.write(", ".join(map(str, strong)))

            # 6. 原始數據
            with st.expander("查看原始數據表格"):
                st.dataframe(df[['期別', '開獎號碼', '超級獎號']], use_container_width=True)
        else:
            st.warning("目前非營業時間或網站維護中。")

st.caption("💡 提示：建議在 07:05 之後使用以獲取當日第一期資料。")
