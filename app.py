"""
AI 菜谱助手 - Web UI (FastAPI 版本)
"""

import os
import json
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from zhipuai import ZhipuAI
import uvicorn

load_dotenv()

app = FastAPI(title="🍳 AI 菜谱助手")

client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

# 对话历史
chat_history = []


def get_html():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍳 AI 菜谱助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #333; margin-bottom: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: white; border: none; cursor: pointer; border-radius: 8px; font-size: 16px; }
        .tab.active { background: #4CAF50; color: white; }
        .panel { display: none; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .panel.active { display: block; }
        textarea { width: 100%; height: 150px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; }
        button { background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        button:hover { background: #45a049; }
        .result { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 15px; white-space: pre-wrap; font-family: monospace; font-size: 13px; }
        #chat-box { height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; background: #fafafa; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 8px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #e8f5e9; }
        input[type="text"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
        input[type="file"] { margin: 10px 0; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍳 AI 菜谱助手</h1>
        
        <div class="tabs">
            <button class="tab active" onclick="showPanel('chat')">💬 对话</button>
            <button class="tab" onclick="showPanel('parse')">📝 菜谱解析</button>
            <button class="tab" onclick="showPanel('image')">📷 图片识别</button>
        </div>
        
        <div id="chat-panel" class="panel active">
            <div id="chat-box"></div>
            <input type="text" id="chat-input" placeholder="输入消息..." onkeypress="if(event.key==='Enter')sendChat()">
            <button onclick="sendChat()">发送</button>
        </div>
        
        <div id="parse-panel" class="panel">
            <textarea id="recipe-text" placeholder="粘贴菜谱内容..."></textarea>
            <button onclick="parseRecipe()">🔍 解析菜谱</button>
            <div id="parse-result" class="result"></div>
        </div>
        
        <div id="image-panel" class="panel">
            <input type="file" id="image-input" accept="image/*">
            <button onclick="analyzeImage()">🔍 识别菜品</button>
            <div id="image-result" class="result"></div>
        </div>
        
        <p style="text-align: center; margin-top: 20px; color: #666;">Powered by 智谱 AI GLM-4</p>
    </div>
    
    <script>
        function showPanel(name) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(name + '-panel').classList.add('active');
        }
        
        async function sendChat() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="message user">${message}</div>`;
            input.value = '';
            
            chatBox.innerHTML += `<div class="message loading" id="loading">思考中...</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });
                const data = await res.json();
                document.getElementById('loading').remove();
                chatBox.innerHTML += `<div class="message assistant">${data.reply}</div>`;
            } catch (e) {
                document.getElementById('loading').textContent = '错误: ' + e.message;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        async function parseRecipe() {
            const text = document.getElementById('recipe-text').value;
            const result = document.getElementById('parse-result');
            result.textContent = '解析中...';
            
            try {
                const res = await fetch('/api/parse', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text})
                });
                const data = await res.json();
                result.textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                result.textContent = '错误: ' + e.message;
            }
        }
        
        async function analyzeImage() {
            const input = document.getElementById('image-input');
            const result = document.getElementById('image-result');
            
            if (!input.files[0]) {
                result.textContent = '请先选择图片';
                return;
            }
            
            result.textContent = '识别中...';
            
            const formData = new FormData();
            formData.append('file', input.files[0]);
            
            try {
                const res = await fetch('/api/image', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                result.textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                result.textContent = '错误: ' + e.message;
            }
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return get_html()


@app.post("/api/chat")
async def chat(request: Request):
    global chat_history
    data = await request.json()
    message = data.get("message", "")
    
    chat_history.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": "你是一个专业的菜谱助手，帮助用户解答烹饪问题。回答要简洁友好。"},
            *chat_history
        ]
    )
    
    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})
    
    # 限制历史长度
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]
    
    return {"reply": reply}


@app.post("/api/parse")
async def parse_recipe(request: Request):
    data = await request.json()
    text = data.get("text", "")
    
    prompt = f"""分析以下菜谱文本，提取结构化信息，返回 JSON：
{text}

返回格式：
{{"name": "菜名", "ingredients": [{{"name": "xxx", "amount": "xxx"}}], "steps": ["步骤1"], "time_minutes": 30}}

只返回 JSON，不要其他文字。"""
    
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    
    try:
        return json.loads(content)
    except:
        return {"error": "解析失败", "raw": content}


@app.post("/api/image")
async def analyze_image(file: UploadFile = File(...)):
    import base64
    from pathlib import Path
    
    # 读取图片
    content = await file.read()
    base64_image = base64.b64encode(content).decode()
    
    # 获取扩展名
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    
    prompt = """分析这张食物图片，返回 JSON：
{"is_food": true/false, "name": "菜名", "ingredients": ["食材"], "cooking_method": "烹饪方式", "tips": "建议"}

只返回 JSON。"""
    
    response = client.chat.completions.create(
        model="glm-4v-flash",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
            ]
        }],
        temperature=0.3
    )
    
    result = response.choices[0].message.content.strip()
    if result.startswith("```"):
        result = result.split("\n", 1)[1]
    if result.endswith("```"):
        result = result.rsplit("```", 1)[0]
    
    try:
        return json.loads(result)
    except:
        return {"error": "解析失败", "raw": result}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
