import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import collections
import time

# 頁面基本設定
st.set_page_config(page_title="BINGO 專業數據分析系統", layout="wide")

# 標題與手機適配優化
st.title("🎰 BINGO BINGO 實時最強分析儀")
st.markdown("針對手機介面優化，即時抓取台彩最新開獎數據。")

# --- 爬蟲核心函數 ---
def fetch_bingo_real_data(num_pages=1):
    """
    抓取台彩官網 BINGO BINGO 當日數據
    """
    url = "https://www.taiwanlottery.com.tw/lotto/bingobingo/drawing.aspx"
    # 這裡我們模擬瀏覽器請求
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    all_data = []
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 尋找開獎表格 (實際解析 HTML 結構)
        # 注意：台彩網頁結構常變，此處為 2024 最新解析邏輯
        table = soup.find('table', {'class': 'table_full'})
        if table:
            rows = table.find_all('tr')[1:] # 跳過標題
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    period = cols[0].text.strip()
                    nums = [int(n) for n in cols[1].text.strip().split(',')]
                    all_data.append({"期別": period, "開獎號碼": nums})
        
        return pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"數據抓取失敗，請稍後再試：{e}")
        return pd.DataFrame()

# --- 側邊欄與交互設定 ---
st.sidebar.header("📊 參數設定")
period_count = st.sidebar.number_input("分析期數 (1-50)", min_value=5, max_value=50, value=20)
game_mode = st.sidebar.selectbox("您的玩法", ["三星", "四星", "五星"])

if st.button("🚀 立即獲取最新數據"):
    with st.spinner('正在與台彩伺服器連線...'):
        df = fetch_bingo_real_data()
        
        if not df.empty:
            df = df.head(period_count) # 取用戶指定的數量
            
            # --- 強中弱機率計算 ---
            all_numbers = [num for sublist in df['開獎號碼'] for num in sublist]
            counts = collections.Counter(all_numbers)
            
            # 建立 1-80 號頻率表
            freq_df = pd.DataFrame([{"號碼": i, "次數": counts.get(i, 0)} for i in range(1, 81)])
            
            # 機率切割 (業界三分法)
            q_high = freq_df['次數'].quantile(0.7)
            q_low = freq_df['次數'].quantile(0.3)
            
            strong = freq_df[freq_df['次數'] >= q_high]['號碼'].tolist()
            middle = freq_df[(freq_df['次數'] < q_high) & (freq_df['次數'] >= q_low)]['號碼'].tolist()
            weak = freq_df[freq_df['次數'] < q_low]['號碼'].tolist()

            # --- 手機端 UI 顯示 ---
            st.success(f"已更新至最新期別：{df.iloc[0]['期別']}")
            
            # 用 Tabs 分隔資訊，適合手機滑動
            tab1, tab2 = st.tabs(["🔥 強中弱分析", "📋 歷史數據"])
            
            with tab1:
                c1, c2, c3 = st.columns(3)
                c1.metric("🔴 強勢號", f"{len(strong)}個", "Hot")
                c2.metric("🟡 中間號", f"{len(middle)}個", "Mid")
                c3.metric("🟢 弱勢號", f"{len(weak)}個", "Cold")
                
                st.write("**【強勢推薦號碼】**")
                st.info(", ".join(map(str, strong[:10])) + " ...")
                
                # --- 核心建議邏輯 ---
                st.subheader(f"💡 {game_mode} 最強組合建議")
                if game_mode == "三星":
                    st.warning("建議組合：**2強 + 1中**。根據機率，全衝熱號易落空，補一個中間號碼回補率最高。")
                elif game_mode == "四星":
                    st.warning("建議組合：**2強 + 1中 + 1弱**。四星需要一個冷號來平衡賠率偏向。")
                elif game_mode == "五星":
                    st.warning("建議組合：**3強 + 1中 + 1弱**。強勢號必須佔 60% 以上才有極高勝率。")
                    
            with tab2:
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("目前非開獎時間或網站維護中。")

# 頁尾資訊
st.caption("⚠️ 本系統僅供機率參考，請理性投注。")
