import streamlit as st
import pandas as pd
import requests
import random
import collections
import re

# --- 頁面配置：專為手機觀看優化 ---
st.set_page_config(page_title="BINGO 數據大師", layout="centered")

# --- 核心爬蟲函數 ---
def get_bingo_data(count=20):
    url = "https://lotto.auzo.tw/bingobingo.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        # 使用 pandas 抓取表格
        dfs = pd.read_html(response.text)
        df = dfs[0]
        
        # 修復：強制取前 4 欄並重新命名，避免 Length mismatch
        df = df.iloc[:, :4] 
        df.columns = ['期別', '開獎號碼', '超級獎號', '猜大小']
        
        # 過濾掉非資料列 (例如標題重複出現的部分)
        df = df[df['期別'].str.contains(r'\d+', na=False)].head(count)
        
        # 處理開獎號碼：將字串轉為數字清單
        def clean_numbers(raw_str):
            # 提取 1-80 之間的數字
            nums = re.findall(r'\d+', str(raw_str))
            return [int(n) for n in nums if 1 <= int(n) <= 80]
            
        df['號碼列表'] = df['開獎號碼'].apply(clean_numbers)
        return df
    except Exception as e:
        st.error(f"數據連線失敗: {e}")
        return pd.DataFrame()

# --- 主畫面介面 ---
st.title("🎰 BINGO 智慧分析儀")
st.caption("數據來源：AUZO 即時網 | 強中弱機率切割")

# 側邊欄參數
num_p = st.sidebar.slider("分析期數", 10, 50, 20)
game_star = st.sidebar.radio("目標玩法", ["三星", "四星", "五星"])

if st.button("🚀 獲取最新強中弱組合", type="primary", use_container_width=True):
    with st.spinner('正在計算數據機率...'):
        df = get_bingo_data(num_p)
        
        if not df.empty:
            # 1. 統計 1-80 號出現頻率
            all_n = [n for sublist in df['號碼列表'] for n in sublist]
            counts = collections.Counter(all_n)
            
            # 2. 強中弱機率切割 (業界 25/50/25 分法)
            sorted_nums = sorted(range(1, 81), key=lambda x: counts[x], reverse=True)
            strong = sorted_nums[:20]  # 前 25% (熱門)
            weak = sorted_nums[-20:]    # 後 25% (冷門)
            middle = [i for i in range(1, 81) if i not in strong and i not in weak]

            # 3. 手機版顯示卡片
            st.success(f"✅ 已抓取最新期：{df.iloc[0]['期別']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🔴 強勢號", f"{len(strong)}個")
            c2.metric("🟡 中間號", f"{len(middle)}個")
            c3.metric("🟢 弱勢號", f"{len(weak)}個")

            # 4. 組合建議邏輯 (業界最強策略)
            st.divider()
            st.subheader(f"💡 {game_star} 組合建議")
            
            def get_suggestion(star, s, m, w):
                # 根據不同星等，分配強中弱比例
                if star == "三星":
                    # 最佳組合：2熱 + 1平
                    pick = random.sample(s, 2) + random.sample(m, 1)
                    return f"建議策略：**2強 + 1中**\n🔥 推薦：`{sorted(pick)}`"
                elif star == "四星":
                    # 最佳組合：2熱 + 1平 + 1冷 (避開官方殺號)
                    pick = random.sample(s, 2) + random.sample(m, 1) + random.sample(w, 1)
                    return f"建議策略：**2強 + 1中 + 1弱**\n🔥 推薦：`{sorted(pick)}`"
                else: # 五星
                    # 最佳組合：3熱 + 1平 + 1冷
                    pick = random.sample(s, 3) + random.sample(m, 1) + random.sample(w, 1)
                    return f"建議策略：**3強 + 1中 + 1弱**\n🔥 推薦：`{sorted(pick)}`"

            st.info(get_suggestion(game_star, strong, middle, weak))
            
            # 5. 數據明細
            with st.expander("查看原始數據 (最新 5 期)"):
                st.table(df[['期別', '開獎號碼']].head(5))
        else:
            st.warning("目前抓不到數據，請檢查網路或是否為開獎時間。")

st.caption("⚠️ 本程式僅供機率研究，不保證獲利，請理性投注。")
