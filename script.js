// 🌐 本地後端 API 的基本網址
const API_BASE_URL = 'https://human-library.onrender.com';

// ==========================================
// 🔍 功能一：心境語義搜尋
// ==========================================
document.getElementById('searchBtn').addEventListener('click', async () => {
    const searchText = document.getElementById('searchText').value.trim();
    const resultsContainer = document.getElementById('searchResults');
    
    if (!searchText) {
        alert('請先輸入您現在的心境或想法喔！');
        return;
    }
    
    resultsContainer.innerHTML = '<p style="color:#7f8c8d; text-align:center;">🔍 AI 正在翻閱圖書館，尋找與你靈魂共鳴的故事...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: searchText }) // 🧠 JavaScript 自動打包成合法 JSON
        });
        
        const data = await response.json();
        resultsContainer.innerHTML = ''; // 清空載入中文字
        
        if (data.status === 'success' && data.results.length > 0) {
            
            // 🌟 調整二：在卡片最上方，動態插入一行「以下是為你推薦的三篇故事」提示文字
            const recommendationTitle = document.createElement('div');
            recommendationTitle.style.cssText = "font-size: 1.1rem; font-weight: bold; color: #2c3e50; margin: 20px 0 10px 0; padding-left: 5px; border-left: 4px solid #2ecc71;";
            recommendationTitle.innerText = "✨ 以下是為您推薦的三篇故事，請享用：";
            resultsContainer.appendChild(recommendationTitle);

            data.results.forEach(story => {
                const card = document.createElement('div');
                card.className = 'story-card';
                
                // 🌟 調整一：契合度數學公式魔法轉換（Sigmoid 函數變形）
                const rawScore = story.score;
                const optimizedScore = 1 / (1 + Math.exp(-10 * (rawScore - 0.35)));
                const displayScore = (optimizedScore * 100).toFixed(1);
                
                card.innerHTML = `
                    <h3>${story.title}</h3>
                    <div class="score">💓 心靈共鳴度：${displayScore}%</div>
                    <p>${story.content}</p>
                `;
                resultsContainer.appendChild(card);
            });
        } else {
            resultsContainer.innerHTML = '<p style="color:#e74c3c; text-align:center;">📭 目前圖書館內還沒有共鳴度足夠的故事，要不要換個說法描述你的困境？</p>';
        }
    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = '<p style="color:#e74c3c; text-align:center;">❌ 無法連線至後端伺服器，請確認 Uvicorn 是否正常執行中。</p>';
    }
});

// ==========================================
// ✍️ 功能二：匿名故事投稿（核心！完美支援多行換行）
// ==========================================
document.getElementById('insertBtn').addEventListener('click', async () => {
    const content = document.getElementById('insertContent').value.trim();
    
    if (!content) {
        alert('故事內容不能為空喔！');
        return;
    }

    
    const originalBtnText = document.getElementById('insertBtn').innerText;
    document.getElementById('insertBtn').innerText = '🚀 AI 排版中...請稍候';
    document.getElementById('insertBtn').disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/insert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const key = data.delete_key; // 拿到憑證
            
            // 🌟 核心魔術：利用瀏覽器 API 自動把憑證塞進使用者的電腦剪貼簿！
            navigator.clipboard.writeText(key).then(() => {
                // 複製成功時的彈窗提示
                alert(`🎉 投稿成功！\n\n🤖 AI 幫您命名的故事標題：\n《${data.title}》\n\n🔑 您的專屬「下架憑證」：\n${key}\n\n💡【系統提示】憑證已自動複製到您的剪貼簿！\n請立刻儲存下來！未來若反悔，可直接「貼上」至下方下架中心永久刪除\n憑證若遺失只能透過連絡我們來下架故事！`);
            }).catch(err => {
                // 防呆：萬一某些極端瀏覽器不支援自動複製，提供備用方案
                alert(`🎉 投稿成功！\n《${data.title}》\n\n憑證為：${key}\n(自動複製失敗，請手動記錄此憑證)`);
            });

            // 清空輸入框
            document.getElementById('insertContent').value = '';
        } else {
            alert('😭 投稿失敗：' + (data.message || '未知錯誤'));
        }
    } catch (error) {
        console.error(error);
        alert('❌ 連線後端失敗，請確認伺服器是否有開啟。');
    } finally {
        document.getElementById('insertBtn').innerText = originalBtnText;
        document.getElementById('insertBtn').disabled = false;
    }
});

// ==========================================
// 🗑️ 功能三：反悔故事下架（修正對齊與防呆版）
// ==========================================
document.getElementById('deleteBtn').addEventListener('click', async () => {
    const deleteKey = document.getElementById('deleteKey').value.trim();
    
    if (!deleteKey) {
        alert('請先輸入您的下架憑證喔！');
        return;
    }
    
    try {
        // 1. 先進刪除前檢查
        const checkResponse = await fetch(`${API_BASE_URL}/api/delete/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delete_key: deleteKey })
        });

        if (!checkResponse.ok) {
            alert('❌ 找不到對應此憑證的故事！請檢查憑證是否輸入錯誤，或該故事先前已被刪除。');
            return; // 🎯 立刻在這裡攔截，絕對不讓它往下衝到確認視窗！
        }
        
        const checkData = await checkResponse.json();
        
        // 🚨 【關鍵防呆】如果後端回傳 None，或者 checkData 根本是 null
        // 或是回傳的資料格式代表找不到故事，就直接攔截！
        if (!checkData || checkData.detail) {
            alert('❌ 找不到對應此憑證的故事！請檢查憑證是否輸入錯誤。');
            return;
        }
        
        // 🌟 【欄位對齊】確保讀取的是後端 `deletenew.py` 回傳的確切欄位
        const storyTitle = checkData.title || "未命名故事";
        const storyPreview = checkData.preview || "無預覽內容";
        
        // 2. 彈窗讓使用者做最後確認
        const confirmDelete = confirm(`⚠️ 系統找到了以下故事：\n\n標題：《${storyTitle}》\n預覽：${storyPreview}\n\n您確定要將這篇故事從圖書館中「永久下架抹除」嗎？此操作無法復原。`);
        
        if (confirmDelete) {
            // 3. 使用者確定要刪，發送確認刪除請求
            const confirmResponse = await fetch(`${API_BASE_URL}/api/delete/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ delete_key: deleteKey })
            });
            
            const confirmData = await confirmResponse.json();
            alert('🧼 ' + (confirmData.message || '故事已成功下架！'));
            document.getElementById('deleteKey').value = '';
        }
    } catch (error) {
        console.error(error);
        alert('❌ 執行下架程序時發生連線錯誤，或找不到該憑證的故事。');
    }
});