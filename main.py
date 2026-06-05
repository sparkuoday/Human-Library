from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import HTTPException, status
from supabase import create_client, Client

# 🔍 精準引入你剛剛修改好的三隻全新模組函式
from querynew import search_single_story
from insertnew import insert_single_story
from deletenew import get_story_preview_for_delete, delete_single_story
import os

# 初始化 FastAPI 應用程式
app = FastAPI(title="虛擬真人圖書館 API 伺服器")

# 🛡️ 跨網域設定 (CORS)
# 可以順利透過瀏覽器發送 fetch 請求給這個後端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 測試與上線初期全開，允許任何網域連線
    allow_credentials=True,
    allow_methods=["*"],  # 允許 GET, POST, OPTIONS 等所有方法
    allow_headers=["*"],  # 允許所有網頁標頭
)

SUPABASE_URL = "https://abxelobavvygfrvybszt.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- 📋 定義前端與後端交換資料的格式 (Pydantic Models) ---

class SearchRequest(BaseModel):
    text: str  # 使用者輸入的心境或問題描述

class InsertRequest(BaseModel):
    content: str  # 使用者在大文字框裡打的完整故事內容

class DeleteRequest(BaseModel):
    delete_key: str  # 使用者輸入的憑證雜湊碼 (Hash)


# --- 🌐 1. 查詢 API 端點 ---
@app.post("/api/search")
def api_search(data: SearchRequest):
    """
    接收使用者的心境，進行單次語義搜尋。
    回傳最接近的 1~3 篇故事完整內容。若無匹配，前端可根據 results 是否為空來顯示提示。
    """
    #matched_stories = search_single_story(data.text)
    matched_stories = search_single_story(data.text, supabase)
    return {
        "status": "success",
        "results": matched_stories
    }


# --- 🌐 2. 投稿 API 端點 ---
@app.post("/api/insert")
def api_insert(data: InsertRequest):
    """
    接收使用者投遞的完整故事，自動進行格式化、AI生成標題與關鍵字、算向量並存檔。
    回傳憑證 (delete_key) 以及下架修改的溫馨警語。
    """
    #response_data = insert_single_story(data.content)
    response_data = insert_single_story(data.content, supabase)
    return response_data


# --- 🌐 3. 刪除前檢查 API 端點 ---
@app.post("/api/delete/check")
async def check_delete(request: DeleteRequest):
    # 呼叫你剛剛改好的 deletenew.py
    #result = get_story_preview_for_delete(request.delete_key)
    result = get_story_preview_for_delete(request.delete_key, supabase)
    
    # 🚨 【關鍵修正】如果 deletenew 找不到故事回傳了 None
    if result is None:
        # 強制讓後端噴出 404 錯誤碼！這樣前端的 checkResponse.ok 就會變成 false，並被成功攔截！
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到對應憑證的故事"
        )
        
    # 如果找到了，就正常回傳 { "title": "...", "preview": "..." }
    return result


# --- 🌐 4. 確認下架刪除 API 端點 ---
@app.post("/api/delete/confirm")
def api_delete_confirm(data: DeleteRequest):
    """
    當使用者在網頁彈窗點擊「確定刪除」後觸發，真正執行刪除檔案與存檔。
    """
    #success, message = delete_single_story(data.delete_key)
    success, message = delete_single_story(data.delete_key, supabase)
    if success:
        return {
            "status": "success",
            "message": message
        }
    else:
        return {
            "status": "error",
            "message": message
        }