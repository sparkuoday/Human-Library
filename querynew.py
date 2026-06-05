import json
from sentence_transformers import SentenceTransformer, util

# --- 1. 全域初始化 (模型與資料庫只載入一次，網頁跑起來才快) ---
model = SentenceTransformer('all-miniLM-L6-v2')

# --- 🎯 核心改動：原本的單次流程，包裝成給網頁用的函式 ---
def search_single_story(user_input: str, db):
    """
    接收前端傳來的查詢字串，進行單次語義搜尋。
    回傳一個包含推薦故事的 list，若無匹配則回傳空 list。
    """
    
    # 2. 讀取 stories.json (每次查詢時讀取最新狀態)
    #try:
    #    with open('stories.json', 'r', encoding='utf-8') as f:
    #        db = json.load(f)
    #except FileNotFoundError:
    #    return []

    # 🌟 核心改動：改向 Supabase 雲端資料庫調閱所有故事資料
    try:
        response = db.table("stories").select("*").execute()
        story_list = response.data  # 這會是一個包著所有故事字典的 List 
    except Exception as e:
        print(f"Supabase 撈取故事失敗: {e}")
        return []

    # 3. 檢查輸入防呆
    user_input = user_input.strip()
    if not user_input:
        return []

    # 4. 進行語義搜尋
    input_vector = model.encode(user_input)
    results = []

    for item in story_list:
        try:
            # 🌟 關鍵核心防呆：如果 Supabase 倒出來的是字串，我們用 json.loads 把它還原成 Python 的數字 List
            current_vector = item['vector']
            if isinstance(current_vector, str):
                current_vector = json.loads(current_vector)
                
            # 計算餘弦相似度
            score = util.cos_sim(input_vector, current_vector).item()
            
            # 遵循你的門檻邏輯 (本機測試建議先調低，上線再調回 0.35)
            if score >= 0.01:
                results.append({
                    "score": score,
                    "title": item.get('title', '未命名故事'),
                    "content": item.get('content', '')
                })
        except Exception as e:
            # 這樣就算某一筆資料有問題，也不會讓整個搜尋當掉！
            print(f"計算這篇故事分數時跳過（原因：{e}）")
            continue

    # 5. 排序並取前三名
    results.sort(key=lambda x: x["score"], reverse=True)
    top_matches = results[:3]

    # 6. 🎯 網頁操作關鍵：直接把最接近的三篇完整內容回傳出去！
    # 網頁端會收到這個 list，並老老實實地呈現在使用者的瀏覽器螢幕上。
    return top_matches