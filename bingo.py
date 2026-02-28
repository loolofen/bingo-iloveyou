import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import pandas as pd
from collections import Counter

app = Flask(__name__)

# --- 1. 抓取資料 (業界最強動態抓取) ---
def get_bingo_data(num_periods=20):
    url = "https://www.taiwanlottery.com.tw/lotto/BINGOBINGO/drawing.aspx"
    # 注意：實際業界會使用 Taiwan Lottery 的 API 或處理 ViewState，此處為邏輯展示
    # 這裡假設抓取回來的資料格式為 [[號碼列表], [號碼列表]...]
    # 為了演示，我們模擬最近的開獎結果
    mock_data = [
        [1, 5, 12, 18, 20, 25, 30, 33, 40, 45, 50, 55, 60, 65, 70, 72, 75, 78, 79, 80],
        # ... 更多期數
    ]
    return mock_data[:num_periods]

# --- 2. 核心算法：強中弱切割 ---
def analyze_probability(data):
    all_nums = [n for period in data for n in period]
    counts = Counter(all_nums)
    
    # 補足 1-80 號，沒出現過的設為 0
    full_counts = {i: counts.get(i, 0) for i in range(1, 81)}
    sorted_nums = sorted(full_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 切割強中弱 (前 25% 強, 中間 50%, 後 25% 弱)
    strong = [n[0] for n in sorted_nums[:20]]
    medium = [n[0] for n in sorted_nums[20:60]]
    weak = [n[0] for n in sorted_nums[60:]]
    
    return strong, medium, weak

# --- 3. 推薦組合邏輯 ---
def get_recommendation(strong, medium, weak, stars):
    # 根據星等給予最強組合建議
    # 策略：高星等(4-5)建議配比：60%強 + 40%中；低星等建議 80%強 + 20%中
    if stars == 5:
        return strong[:3] + medium[:2]
    elif stars == 4:
        return strong[:3] + medium[:1]
    else: # 三星
        return strong[:2] + medium[:1]

@app.route('/', methods=['GET', 'POST'])
def index():
    recommend = None
    strong, medium, weak = [], [], []
    periods = 50
    stars = 3
    
    if request.method == 'POST':
        periods = int(request.form.get('periods', 50))
        stars = int(request.form.get('stars', 3))
        
        raw_data = get_bingo_data(periods)
        strong, medium, weak = analyze_probability(raw_data)
        recommend = get_recommendation(strong, medium, weak, stars)
        
    return render_template('index.html', strong=strong, medium=medium, 
                           weak=weak, recommend=recommend, periods=periods, stars=stars)

if __name__ == '__main__':
    app.run(debug=True)