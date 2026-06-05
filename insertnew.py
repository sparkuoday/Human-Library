import os
import json
import re
import hashlib
import time
from openai import OpenAI
from postgrest.exceptions import APIError

# --- 1. 全域初始化 (維持你的設定，避免重複載入模型) ---
# 這裡維持你原本圖片中的金鑰與模型設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#embedding_model = SentenceTransformer('all-miniLM-L6-v2')
DB_FILE = 'stories.json'


def get_openai_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# --- 2. 自動文字排版與清理功能 (完全保留你的邏輯) ---
def parse_and_format_content(text):
    """
    根據逗號、句號、問號、驚嘆號與空格進行智慧換行排版，方便人類閱讀。
    """
    # 先將多餘的連續換行縮減為單一換行（維持你第 22 行的優秀原創）
    text = re.sub(r'\n+', '\n', text).strip()

    # 💡 乾淨、精準的標點引號黏著規則 (避免了中括號內不小心混入的空格)
    # 意思是：匹配任何 ［。？！］，且如果後面緊跟著 ［」”〉］也一併算進去。
    pattern = r'([。？！][」』”〉]?)'

    # 🌟 大絕招：利用 re.sub 搭配「正向預查」，只要後面不是換行（\n），就在後面塞一個 \n
    # 這樣做絕對不會吃掉標點符號，還會把段落排得超級漂亮！
    text = re.sub(pattern, r'\1\n', text)

    # 防呆：萬一補完 \n 之後造成連續換行，再做一次單一化清洗
    text = re.sub(r'\n+', '\n', text).strip()

    return text


# --- 3. 呼叫 LLM 生成標題與關鍵字 (完全保留你的邏輯) ---
def get_llm_metadata(content):
    prompt = f"""
    請針對以下故事內容，生成一個 30 字左右、有溫度的標題，並提取 3 個最核心的關鍵字（Keyword）。
    請嚴格以下列 JSON 格式回傳：
    {{
      "title": "這裡寫生成的標題",
      "keywords": ["關鍵字1", "關鍵字2", "關鍵字3"]
    }}

    故事內容：
    {content}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini", # 便宜又強大的模型
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" } # 強烈要求回傳標準 JSON
    )
    result = json.loads(response.choices[0].message.content)
    return result['title'], result['keywords']


# --- 4. 生成唯一的刪除憑證 (完全保留你的邏輯) ---
def generate_delete_hash(title, content):
    """
    利用動態標題、內容片段、以及當前時間戳進行 SHA-256 加密。
    """
    timestamp = str(time.time())
    # 取內文前 50 個 byte 和後 50 個 byte 的組合
    content_bytes = content.encode('utf-8')
    start_part = content_bytes[:50]
    end_part = content_bytes[-50:] if len(content_bytes) > 50 else b""
    
    # 混合「標題 + 時間 + 內容前後段」進行雜湊
    hasher = hashlib.sha256()
    hasher.update(title.encode('utf-8'))
    hasher.update(timestamp.encode('utf-8'))
    hasher.update(start_part + end_part)
    
    # 取前 16 位碼作為給使用者的簡短金鑰
    return f"HL-{hasher.hexdigest()[:16].upper()}"


# --- 🎯 核心改動：轉化為給 FastAPI 呼喚的單次處理函式 ---
def insert_single_story(raw_content: str, db):
    """
    單次投稿處理。由網頁傳入整坨故事文字，處理完後直接寫入 JSON。
    """
    # 基本防呆
    if not raw_content.strip():
        return {"status": "error", "message": "內容不能為空，投稿失敗。"}

    # [1/4] 智慧排版優化
    formatted_content = parse_and_format_content(raw_content)
    
    # [2/4] 呼叫 AI 生成標題與關鍵字
    try:
        title, keywords = get_llm_metadata(formatted_content)
    except Exception as e:
        title = "無題的生命故事"
        keywords = ["真人故事"]
        
    # [3/4] 計算綜合語義向量
    rich_text_for_vector = f"標題：{title}。關鍵字：{', '.join(keywords)}。內容：{formatted_content}"
    vector_data = get_openai_embedding(rich_text_for_vector)
    
    # [4/4] 生成安全的刪除憑證
    delete_hash = generate_delete_hash(title, formatted_content)
    
    # 打包成最終資料結構 (完全對應你原本的 JSON 欄位)
    new_story = {
        "title": title,
        "keywords": keywords,
        "content": formatted_content,
        "vector": vector_data,
        "delete_key": delete_hash
    }
    
    # 讀取並寫入 stories.json
    #if os.path.exists(DB_FILE):
    #    with open(DB_FILE, 'r', encoding='utf-8') as f:
    #        db = json.load(f)
    #else:
    #    db = []
        
    #db.append(new_story)
    
    #with open(DB_FILE, 'w', encoding='utf-8') as f:
    #    json.dump(db, f, ensure_ascii=False, indent=2)
        
    # 🌟 網頁貼心設計：除了給他 Hash，順便把你想在螢幕上顯示的警語一起回傳

    try:
        db.table("stories").insert(new_story).execute()
    except Exception as e:
        print(f"Supabase 寫入爆了：{e}")
        return {"status": "error", "message": f"雲端資料庫同步失敗: {str(e)}"}
    
    return {
        "status": "success",
        "title": title,
        "delete_key": delete_hash,
        "notice": "如果你發現投稿內容有誤想修改，請先用此憑證刪除再重新投稿。"
    }