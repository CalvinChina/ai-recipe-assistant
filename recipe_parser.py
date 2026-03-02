"""
菜谱解析器 - 将文本解析为结构化 JSON
"""

import json
import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

# System Prompt - 定义 AI 的行为和输出格式
SYSTEM_PROMPT = """你是一个专业的菜谱分析助手。

## 任务
分析用户提供的菜谱文本，提取结构化信息。

## 输出格式
必须返回纯 JSON（不要 markdown 代码块），格式如下：
{
    "name": "菜名",
    "ingredients": [
        {"name": "食材名", "amount": "用量"}
    ],
    "steps": ["步骤1", "步骤2", "步骤3"],
    "difficulty": "简单/中等/困难",
    "time_minutes": 30,
    "tags": ["标签1", "标签2"]
}

## 限制
- 只返回 JSON，不要任何其他文字
- 食材必须包含用量（如果原文没有，合理估算）
- 步骤要具体可操作，每步一个字符串
- time_minutes 是总耗时（分钟）
- tags 包括菜系、口味、场景等"""


def parse_recipe(client: ZhipuAI, text: str) -> dict:
    """
    解析菜谱文本为结构化数据
    
    Args:
        client: ZhipuAI 客户端
        text: 菜谱文本
        
    Returns:
        解析后的 JSON 数据
    """
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请解析以下菜谱：\n\n{text}"}
        ],
        temperature=0.3,  # 降低随机性，输出更稳定
    )
    
    content = response.choices[0].message.content.strip()
    
    # 移除可能的 markdown 代码块标记
    if content.startswith("```"):
        content = content.split("\n", 1)[1]  # 移除第一行
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]  # 移除最后的 ```
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"原始内容: {content}")
        return None


def main():
    """测试菜谱解析"""
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请先设置 ZHIPU_API_KEY")
        return
    
    client = ZhipuAI(api_key=api_key)
    
    # 测试用例
    test_recipes = [
        """
        红烧肉
        
        食材：五花肉 500克，冰糖 30克，生抽 2勺，老抽 1勺，料酒 2勺，葱姜适量
        
        做法：
        1. 五花肉切块，冷水下锅焯水去血沫
        2. 锅中放少许油，加入冰糖炒糖色
        3. 放入五花肉翻炒上色
        4. 加入葱姜、料酒、生抽、老抽
        5. 加水没过肉，大火烧开转小火炖1小时
        6. 大火收汁即可
        """,
        
        """
        番茄炒蛋很简单，拿两个番茄切块，三个鸡蛋打散。
        先炒鸡蛋盛出来，再炒番茄出汁，把鸡蛋倒回去一起翻炒，加盐调味就好。
        大概10分钟能做好。
        """
    ]
    
    print("🍳 菜谱解析测试\n")
    print("=" * 50)
    
    for i, recipe_text in enumerate(test_recipes, 1):
        print(f"\n📝 测试 {i}:")
        print("-" * 30)
        
        result = parse_recipe(client, recipe_text)
        
        if result:
            print(f"✅ 解析成功！\n")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("❌ 解析失败")
        
        print("=" * 50)


if __name__ == "__main__":
    main()
