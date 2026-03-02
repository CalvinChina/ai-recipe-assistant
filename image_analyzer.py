"""
图片识别器 - 使用 GLM-4V 识别菜品和食材
"""

import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()


class ImageAnalyzer:
    """图片分析器"""
    
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ZHIPU_API_KEY")
        
        self.client = ZhipuAI(api_key=self.api_key)
    
    def encode_image(self, image_path: str) -> tuple[str, str]:
        """
        将图片编码为 base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            (base64字符串, MIME类型)
        """
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的图片格式: {ext}")
        
        # MIME 类型映射
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        
        with open(path, "rb") as f:
            image_data = f.read()
        
        base64_str = base64.b64encode(image_data).decode("utf-8")
        mime_type = mime_map[ext]
        
        return base64_str, mime_type
    
    def analyze_dish(self, image_path: str) -> dict:
        """
        识别菜品图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            菜品信息
        """
        print(f"📷 正在分析图片: {image_path}")
        
        # 编码图片
        base64_image, mime_type = self.encode_image(image_path)
        print(f"✅ 图片加载成功 ({mime_type})")
        
        # 调用 GLM-4V
        print("🤖 正在识别菜品...")
        
        prompt = """分析这张食物图片，返回 JSON 格式：

{
    "is_food": true/false,
    "name": "菜名（如果是食物）",
    "description": "描述这道菜的外观特点",
    "likely_ingredients": ["推测的主要食材"],
    "cooking_method": "推测的烹饪方式（炒/蒸/煮/烤等）",
    "difficulty": "简单/中等/困难",
    "estimated_time": "预计烹饪时间（分钟）",
    "tips": "一个烹饪小建议"
}

注意：
- 只返回 JSON，不要其他文字
- 如果不是食物，is_food 设为 false，name 可以不填
- 尽量识别出具体菜名"""

        response = self.client.chat.completions.create(
            model="glm-4v-flash",  # 视觉模型
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        
        # 清理 markdown
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        
        try:
            result = json.loads(content)
            result["image_path"] = image_path
            print("✅ 识别完成！")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return {"error": "解析失败", "raw": content}
    
    def identify_ingredients(self, image_path: str) -> dict:
        """
        识别食材图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            食材信息
        """
        print(f"📷 正在分析食材: {image_path}")
        
        base64_image, mime_type = self.encode_image(image_path)
        print(f"✅ 图片加载成功 ({mime_type})")
        
        print("🤖 正在识别食材...")
        
        prompt = """分析这张图片中的食材，返回 JSON 格式：

{
    "ingredients": [
        {
            "name": "食材名称",
            "quantity": "数量（如果能判断）",
            "freshness": "新鲜度评估（新鲜/一般/不新鲜）"
        }
    ],
    "possible_dishes": ["用这些食材可以做的3道菜"],
    "shopping_suggestions": ["缺少的配料建议"]
}

注意：
- 只返回 JSON
- 尽可能识别所有可见的食材
- 如果不是食材图片，返回 {"error": "不是食材图片"}"""

        response = self.client.chat.completions.create(
            model="glm-4v-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        
        try:
            result = json.loads(content)
            result["image_path"] = image_path
            print("✅ 识别完成！")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return {"error": "解析失败", "raw": content}


def main():
    """交互式图片分析"""
    analyzer = ImageAnalyzer()
    
    print("📷 图片识别器")
    print("=" * 50)
    print("1. 识别菜品")
    print("2. 识别食材")
    print("=" * 50)
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice not in ["1", "2"]:
        print("❌ 无效选择")
        return
    
    image_path = input("请输入图片路径: ").strip()
    
    # 去掉可能的引号
    image_path = image_path.strip("\"'")
    
    if not image_path:
        print("❌ 路径不能为空")
        return
    
    try:
        if choice == "1":
            result = analyzer.analyze_dish(image_path)
        else:
            result = analyzer.identify_ingredients(image_path)
        
        print("\n📋 分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ 分析失败: {e}")


if __name__ == "__main__":
    main()
