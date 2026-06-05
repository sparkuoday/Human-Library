import json
import os

DB_FILE = 'stories.json'

def get_story_preview_for_delete(user_hash: str, db):
    """
    【刪除前檢查】
    根據憑證比對故事。如果找到，回傳標題與預覽；找不到則回傳 None。
    """
    user_hash = user_hash.strip().upper()
    if not user_hash:
        return None

    #try:
    #    with open(DB_FILE, 'r', encoding='utf-8') as f:
    #        db = json.load(f)
    #except Exception:
    #    return None

    # 尋找匹配的故事
    #for item in db:
    #    if "delete_key" in item and item["delete_key"].strip().upper() == user_hash:
    #        # 擷取前 50 個字當作預覽，並把換行置換成空格
    #        preview_text = item['content'][:50].replace('\n', ' ') + "..."
            
            # 🚨 這裡最關鍵！回傳的字典 Key 值必須是 'title' 和 'preview'

    try:
        # 🌟 核心大改動：直接命令 Supabase 尋找 delete_key 等於 user_hash 的資料
        response = db.table("stories").select("title", "content").eq("delete_key", user_hash).execute()
        
        # 如果沒撈到資料，代表憑證不存在
        if not response.data:
            return None
            
        # 抓出符合的那筆故事
        story = response.data[0]
        
        # 🌟 完美保留你原本的「擷取前 50 字預覽並把換行換成空格」的貼心設計！
        preview_text = story['content'][:50].replace('\n', ' ') + "..."
        
        return {
            "title": story['title'],
            "preview": preview_text
        }
    except Exception as e:
        print(f"Supabase 檢查刪除時發生錯誤: {e}")
        return None
            
            
    #        return {
    #            "title": item['title'],
    #            "preview": preview_text
    #        }
    
    #return None


def delete_single_story(user_hash: str, db):
    """
    【執行安全刪除】
    從 JSON 中移除該筆資料並重新寫入。
    """
    user_hash = user_hash.strip().upper()
    if not user_hash:
        return False, "資料庫檔案不存在或憑證為空"
    
    try:
        # 🌟 核心大改動：先檢查雲端這筆資料還在不在（怕別人同時刪除）
        check_response = db.table("stories").select("id").eq("delete_key", user_hash).execute()
        if not check_response.data:
            return False, "找不到對應此憑證的故事，可能已被刪除。"

        # 🌟 一行搞定：直接去雲端刪除符合 delete_key 的該筆故事
        db.table("stories").delete().eq("delete_key", user_hash).execute()
        
        # 🌟 完美保留你原本的溫馨成功語句！
        return True, "故事已成功從圖書館中永久下架！"
        
    except Exception as e:
        print(f"Supabase 執行刪除時發生錯誤: {e}")
        return False, f"刪除失敗: {str(e)}"

    #try:
    #    with open(DB_FILE, 'r', encoding='utf-8') as f:
    #        db = json.load(f)
    #except Exception as e:
    #    return False, f"讀取資料庫失敗: {str(e)}"

    #target_index = -1
    #for index, item in enumerate(db):
    #    if "delete_key" in item and item["delete_key"].strip().upper() == user_hash:
    #        target_index = index
    #        break

    # 如果找到了，就從 list 中移除並存檔
    #if target_index != -1:
    #    db.pop(target_index)
    #    try:
    #        with open(DB_FILE, 'w', encoding='utf-8') as f:
    #            json.dump(db, f, ensure_ascii=False, indent=2)
    #        return True, "故事已成功從圖書館中永久下架！"
    #    except Exception as e:
    #        return False, f"寫入資料庫失敗: {str(e)}"
    
    #return False, "找不到對應此憑證的故事，可能已被刪除。"