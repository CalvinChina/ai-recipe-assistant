"""
多轮对话助手 - 带上下文记忆
"""

import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from typing import List

load_dotenv()


class ConversationAssistant:
    """带记忆的对话助手"""
    
    def __init__(self, api_key: str = None):
        """
        初始化助手
        
        Args:
            api_key: API Key，默认从环境变量读取
        """
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ZHIPU_API_KEY")
        
        self.client = ZhipuAI(api_key=self.api_key)
        
        # 对话历史 - 核心：存储上下文
        self.messages: List[dict] = []
        
        # 系统提示词
        self.system_prompt = """你是一个专业的菜谱助手，帮助用户解答烹饪问题。

## 能力
- 推荐菜谱
- 解释做法
- 提供烹饪技巧
- 根据食材推荐菜品

## 风格
- 亲切友好
- 回答简洁（100字以内）
- 如果不确定，诚实说不知道"""
    
    def chat(self, user_input: str) -> str:
        """
        发送消息并获取回复
        
        Args:
            user_input: 用户输入
            
        Returns:
            AI 回复
        """
        # 1. 添加用户消息到历史
        self.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 2. 构建完整消息列表（系统提示 + 历史对话）
        full_messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.messages
        
        # 3. 调用 API
        response = self.client.chat.completions.create(
            model="glm-4-flash",
            messages=full_messages,
            temperature=0.7,  # 稍高一点，对话更自然
        )
        
        # 4. 提取回复
        assistant_reply = response.choices[0].message.content
        
        # 5. 添加助手回复到历史（重要！下次对话才能记住）
        self.messages.append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        return assistant_reply
    
    def clear_history(self):
        """清空对话历史"""
        self.messages = []
        print("🗑️ 对话历史已清空")
    
    def show_history(self):
        """显示对话历史"""
        if not self.messages:
            print("暂无对话历史")
            return
        
        print("\n📜 对话历史:")
        print("-" * 40)
        for msg in self.messages:
            role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
            print(f"{role}: {msg['content'][:50]}...")
        print("-" * 40)
    
    def get_token_count(self) -> int:
        """估算 token 数量（简单估算：中文约 1.5 字/token）"""
        total_chars = sum(len(msg["content"]) for msg in self.messages)
        return int(total_chars / 1.5)


def main():
    """交互式对话"""
    assistant = ConversationAssistant()
    
    print("🍳 AI 菜谱助手（多轮对话版）")
    print("=" * 40)
    print("命令:")
    print("  /clear  - 清空对话历史")
    print("  /history - 查看对话历史")
    print("  /tokens  - 查看 token 使用量")
    print("  quit    - 退出")
    print("=" * 40)
    print()
    
    while True:
        try:
            user_input = input("👤 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        
        # 处理命令
        if user_input == "quit":
            print("再见！")
            break
        elif user_input == "/clear":
            assistant.clear_history()
            continue
        elif user_input == "/history":
            assistant.show_history()
            continue
        elif user_input == "/tokens":
            print(f"📊 估算 token: {assistant.get_token_count()}")
            continue
        
        if not user_input:
            continue
        
        # 正常对话
        reply = assistant.chat(user_input)
        print(f"\n🤖 助手: {reply}\n")


if __name__ == "__main__":
    main()
