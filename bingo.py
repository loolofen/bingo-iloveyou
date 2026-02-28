import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import collections
import random

# --- 頁面配置：專為手機觀看優化 ---
st.set_page_config(page_title="BINGO 數據大師 (AUZO版)", layout="centered")

# 增加一點美化 CSS
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 5px; background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 核心爬蟲：抓取 lotto.auzo.tw ---
def fetch_auzo_bingo(count=20):
    url = "https://lotto.auzo.tw/bingobingo.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找開獎表格 (該站點結構：通常在第1個 table)
        table = soup.find('table')
        rows = table.find_all('tr')[1:] # 跳過表頭
        
        data = []
        for row in rows[:count]:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # 抓取期號與開獎號碼
                period = cols[0].get_text(strip=True)
                # 該網站號碼通常在第二格，且有特定格式
                nums_text = cols[1].get_text(strip=True)
                # 提取出數字（過濾掉非數字字符）
                import re
                num_list = [int(n) for n in re.findall(r'\d+', nums_text) if int(n) <= 80]
                
                if num_list:
                    data.append({"期別": period, "號碼": num_list})
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"數據讀取失敗：{e}")
        return pd.DataFrame()

# --- 主程式邏輯 ---
st.title("🎰 BINGO 智慧分析儀")
st.caption("數據來源：AUZO 即時樂透網")

# 側邊欄參數設定
num_periods = st.sidebar.slider("分析期數", 10, 50, 20)
play_style = st.sidebar.radio("目標模式", ["三星", "四星", "五星"])

if st.button("🔄 立即抓取最新數據並分析", use_container_width=True):
    with st.spinner('正在分析 AUZO 即時數據...'):
        df = fetch_auzo_bingo(num_periods)
        
        if not df.empty:
            # 1. 數據分析
            all_nums = [n for sub in df['號碼'] for n in sub]
            freq = collections.Counter(all_nums)
            
            # 2. 強中弱邏輯切割 (機率切割)
            # 根據出現次數排序 1-80 號
            sorted_nums = sorted(range(1, 81), key=lambda x: freq[x], reverse=True)
            strong = sorted_nums[:20]  # 熱門 (前 25%)
            weak = sorted_nums[-20:]    # 冷門 (後 25%)
            middle = [i for i in range(1, 81) if i not in strong and i not in weak]

            # 3. 顯示 UI (手機卡片式設計)
            st.success(f"已同步至最新期別：{df.iloc[0]['期別']}")
            
            t1, t2 = st.tabs(["🔥 組合建議", "📊 數據報表"])
            
            with t1:
                # 組合建議核心邏輯
                st.subheader(f"💡 {play_style} 最佳配置")
                
                def get_rec(mode, s, m, w):
                    if mode == "三星":
                        # 2強 + 1中：穩健型
                        return f"2強勢 + 1中間 👉 **{sorted(random.sample(s, 2) + random.sample(m, 1))}**"
                    elif mode == "四星":
                        # 2強 + 1中 + 1弱：避險型
                        return f"2強勢 + 1中間 + 1弱勢 👉 **{sorted(random.sample(s, 2) + random.sample(m, 1) + random.sample(w, 1))}**"
                    else:
                        # 3強 + 1中 + 1弱：激進型
                        return f"3強勢 + 1中間 + 1弱勢 👉 **{sorted(random.sample(s, 3) + random.sample(m, 1) + random.sample(w, 1))}**"
                
                st.info(get_rec(play_style, strong, middle, weak))
                
                # 強中弱號碼分布
                col1, col2, col3 = st.columns(3)
                col1.metric("🔴 強勢熱號", f"{strong[0]}")
                col2.metric("🟡 中間平衡", f"{middle[0]}")
                col3.metric("🟢 弱勢冷號", f"{weak[0]}")
                st.write("**當前最強勢 10 碼：**", strong[:10])

            with t2:
                st.write("歷史紀錄 (最新排在最前)")
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("暫時抓不到數據，請確認現在是否為 07:05 ~ 23:55 (開獎時間)。")

st.divider()
st.caption("本工具僅供機率參考。提醒您：小賭怡情，大賭傷神。")
