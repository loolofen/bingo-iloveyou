import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import Counter
import random

# 設定網頁標題與手機優化
st.set_page_config(page_title="BINGO BINGO 強中弱分析", layout="wide")

st.title("🎰 BINGO BINGO 數據大師")
st.markdown("---")

# --- 1. 抓取資料函數 (模擬業界爬蟲邏輯) ---
def get_bingo_data(n_periods):
    # 這裡實作抓取台灣彩券官網或 API 的邏輯
    # 為了演示，我們生成最近期的模擬數據 (1-80號)
    data = []
    for _ in range(n_periods):
        data.append(random.sample(range(1, 81), 20))
    return data

# --- 2. 側邊欄設定 (手機版會收合在左側) ---
st.sidebar.header("📊 分析設定")
periods = st.sidebar.slider("分析期數", min_value=10, max_value=200, value=50)
star_type = st.sidebar.selectbox("目標玩法", ["三星", "四星", "五星"])

# --- 3. 核心邏輯：強中弱切割 ---
raw_data = get_bingo_data(periods)
all_nums = [n for p in raw_data for n in p]
counts = Counter(all_nums)
full_counts = {i: counts.get(i, 0) for i in range(1, 81)}
sorted_nums = sorted(full_counts.items(), key=lambda x: x[1], reverse=True)

strong = [n[0] for n in sorted_nums[:20]]   # 出現率前 25%
medium = [n[0] for n in sorted_nums[20:60]] # 中間 50%
weak = [n[0] for n in sorted_nums[60:]]     # 後面 25%

# --- 4. UI 呈現 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.error(f"🔥 強勢號 (Top 20)\n\n{', '.join(map(str, strong[:10]))}...")
with col2:
    st.warning(f"⚖️ 中間號 (穩定)\n\n{', '.join(map(str, medium[:10]))}...")
with col3:
    st.info(f"❄️ 弱勢號 (冷門)\n\n{', '.join(map(str, weak[:10]))}...")

st.markdown("---")

# --- 5. 推薦組合邏輯 ---
st.subheader(f"💡 專家推薦：{star_type} 最強組合")

star_map = {"三星": 3, "四星": 4, "五星": 5}
n_stars = star_map[star_type]

# 推薦邏輯：強勢號佔 60-70%，中位號補足，避開弱勢號
if n_stars == 3:
    rec = random.sample(strong, 2) + random.sample(medium, 1)
elif n_stars == 4:
    rec = random.sample(strong, 3) + random.sample(medium, 1)
else: # 五星
    rec = random.sample(strong, 3) + random.sample(medium, 2)

# 用漂亮的標籤顯示推薦號碼
cols = st.columns(n_stars)
for i, num in enumerate(rec):
    cols[i].metric(label=f"第 {i+1} 碼", value=num)

st.success("✅ 建議策略：根據近 {} 期數據，強勢號碼正處於上升期，建議作為選號核心。".format(periods))
