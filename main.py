"""
AI Recipe Assistant - 智能菜谱助手
"""

import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 加载环境变量
load_dotenv()


def main():
    """主函数"""
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请先设置 ZHIPU_API_KEY 环境变量")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 填入你的 API Key")
        return

    client = ZhipuAI(api_key=api_key)

    print("🍳 AI 菜谱助手")
    print("输入 'quit' 退出\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() == "quit":
            print("再见！")
            break

        if not user_input:
            continue

        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个专业的菜谱助手，帮助用户解答烹饪问题。"},
                {"role": "user", "content": user_input}
            ],
        )

        print(f"\n助手: {response.choices[0].message.content}\n")


if __name__ == "__main__":
    main()
