import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import collections
import random

# --- 頁面優化 ---
st.set_page_config(page_title="BINGO 數據大師 - 實戰修復版", layout="wide")

# --- 業界穩定版爬蟲 (解析 HTML) ---
def fetch_bingo_html_data(count=20):
    # 改用官方開獎公告網址，這是最難被擋的
    url = "https://www.taiwanlottery.com.tw/lotto/bingobingo/drawing.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 強制編碼避免亂碼
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尋找開獎資料表格 (根據台彩目前的網頁結構)
            # BINGO 號碼通常在 class 為 'table_full' 的表格中
            table = soup.find('table', {'class': 'table_full'})
            if not table:
                # 備援尋找方式
                table = soup.find('table')
            
            rows = table.find_all('tr')[1:] # 跳過表頭
            
            final_list = []
            for row in rows[:count]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    period = cols[0].get_text(strip=True)
                    # 號碼通常是用逗號分隔或是連續數字
                    raw_nums = cols[1].get_text(strip=True).replace('\xa0', ' ').replace(',', ' ')
                    num_list = [int(n) for n in raw_nums.split() if n.isdigit()]
                    
                    if num_list:
                        final_list.append({
                            "期別": period,
                            "號碼": num_list
                        })
            return pd.DataFrame(final_list)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"連線異常，請檢查網路或是否為非營業時間。")
        return pd.DataFrame()

# --- 介面實作 ---
st.title("🎰 BINGO 強中弱策略機 (修復版)")

# 側邊欄設定
num_to_fetch = st.sidebar.slider("分析期數", 10, 50, 20)
game_choice = st.sidebar.radio("目標玩法", ["三星", "四星", "五星"])

if st.button("🚀 獲取最新開獎並分析", use_container_width=True):
    with st.spinner('連線至台彩官網中...'):
        df = fetch_bingo_html_data(num_to_fetch)
        
        if not df.empty:
            # 1. 計算頻率 (1-80號)
            all_nums = [n for sub in df['號碼'] for n in sub]
            freq = collections.Counter(all_nums)
            
            # 2. 強中弱切割
            sorted_nums = sorted(range(1, 81), key=lambda x: freq[x], reverse=True)
            strong = sorted_nums[:20] 
            weak = sorted_nums[-20:]
            middle = [i for i in range(1, 81) if i not in strong and i not in weak]

            # 3. 顯示結果
            st.success(f"✅ 已抓取最新期別：{df.iloc[0]['期別']}")
            
            tab1, tab2 = st.tabs(["🔥 策略建議", "📊 數據報表"])
            
            with tab1:
                c1, c2, c3 = st.columns(3)
                c1.metric("🔴 強勢號", f"{strong[0]},{strong[1]}")
                c2.metric("🟡 中間號", f"{middle[0]},{middle[1]}")
                c3.metric("🟢 弱勢號", f"{weak[0]},{weak[1]}")
                
                st.divider()
                
                # 組合建議邏輯
                if game_choice == "三星":
                    rec = random.sample(strong, 2) + random.sample(middle, 1)
                    st.info(f"建議：2強 + 1中 👉 **{sorted(rec)}**")
                elif game_choice == "四星":
                    rec = random.sample(strong, 2) + random.sample(middle, 1) + random.sample(weak, 1)
                    st.info(f"建議：2強 + 1中 + 1弱 👉 **{sorted(rec)}**")
                elif game_choice == "五星":
                    rec = random.sample(strong, 3) + random.sample(middle, 1) + random.sample(weak, 1)
                    st.info(f"建議：3強 + 1中 + 1弱 👉 **{sorted(rec)}**")
            
            with tab2:
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("抓不到資料！請確認目前是否為 07:00 ~ 24:00。")
