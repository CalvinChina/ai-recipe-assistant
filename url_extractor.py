"""
URL 菜谱提取器 - 从网页提取菜谱信息
"""

import json
import os
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()


class RecipeExtractor:
    """从 URL 提取菜谱"""
    
    # 常见菜谱网站
    RECIPE_SITES = {
        "xiachufang.com": "下厨房",
        "meishij.net": "美食杰",
        "haodou.com": "好豆",
        "xinshipu.com": "心食谱",
        "douguo.com": "豆果美食",
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ZHIPU_API_KEY")
        
        self.client = ZhipuAI(api_key=self.api_key)
        
        # 请求头，模拟浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
    
    def fetch_webpage(self, url: str) -> str:
        """
        获取网页内容
        
        Args:
            url: 网页 URL
            
        Returns:
            网页文本内容
        """
        try:
            # 更完整的请求头
            headers = {
                **self.headers,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # 检测编码
            if response.encoding == "ISO-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"
            
            print(f"   状态码: {response.status_code}")
            print(f"   编码: {response.encoding}")
            
            return response.text
        except requests.RequestException as e:
            raise Exception(f"获取网页失败: {e}")
    
    def extract_text(self, html: str) -> str:
        """
        从 HTML 提取纯文本
        
        Args:
            html: HTML 内容
            
        Returns:
            提取的文本
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 移除不需要的标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        # 获取文本
        text = soup.get_text(separator="\n")
        
        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)
        
        return text
    
    def extract_recipe(self, url: str) -> dict:
        """
        从 URL 提取菜谱信息
        
        Args:
            url: 菜谱网页 URL
            
        Returns:
            结构化菜谱数据
        """
        print(f"🌐 正在获取网页: {url}")
        
        # 1. 获取网页
        html = self.fetch_webpage(url)
        print(f"✅ 网页获取成功 ({len(html)} 字符)")
        
        # 2. 提取文本
        text = self.extract_text(html)
        print(f"📝 文本提取成功 ({len(text)} 字符)")
        
        # 3. 截取前 3000 字符（避免 token 超限）
        if len(text) > 3000:
            text = text[:3000] + "\n...(内容过长已截断)"
        
        # 4. 用 LLM 提取菜谱信息
        print("🤖 正在分析菜谱...")
        recipe = self._parse_with_llm(text, url)
        
        if recipe:
            recipe["source_url"] = url
            print("✅ 菜谱提取成功！")
        
        return recipe
    
    def _parse_with_llm(self, text: str, url: str) -> dict:
        """用 LLM 解析菜谱"""
        
        # 检测网站
        domain = urlparse(url).netloc
        site_name = next(
            (name for d, name in self.RECIPE_SITES.items() if d in domain),
            "未知网站"
        )
        
        prompt = f"""从以下网页文本中提取菜谱信息。

来源网站: {site_name}
URL: {url}

网页内容:
{text}

请提取菜谱信息，返回 JSON 格式：
{{
    "name": "菜名",
    "ingredients": [
        {{"name": "食材名", "amount": "用量"}}
    ],
    "steps": ["步骤1", "步骤2"],
    "difficulty": "简单/中等/困难",
    "time_minutes": 估算时间,
    "tags": ["标签1", "标签2"],
    "tips": "小贴士（如果有）"
}}

注意：
- 只返回 JSON，不要其他文字
- 如果不是菜谱页面，返回 {{"error": "不是菜谱页面", "name": null}}
- 用量如果原文没有，写"适量"
- 步骤要完整，不要遗漏"""

        response = self.client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        
        # 清理 markdown
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return {"error": "解析失败", "raw": content}


def main():
    """测试 URL 提取"""
    extractor = RecipeExtractor()
    
    print("🍳 菜谱提取器")
    print("=" * 50)
    print("1. 从 URL 提取")
    print("2. 从粘贴的文本提取")
    print("=" * 50)
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        url = input("请输入菜谱 URL: ").strip()
        if not url:
            print("❌ URL 不能为空")
            return
        
        try:
            recipe = extractor.extract_recipe(url)
            
            if recipe.get("error"):
                print(f"\n❌ {recipe['error']}")
                if recipe.get("raw"):
                    print(f"原始内容: {recipe['raw'][:200]}...")
            else:
                print("\n📋 提取结果:")
                print(json.dumps(recipe, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 提取失败: {e}")
    
    elif choice == "2":
        print("\n请粘贴菜谱内容（输入空行结束）:")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        text = "\n".join(lines)
        
        if len(text) < 10:
            print("❌ 内容太短")
            return
        
        print("\n🤖 正在分析...")
        recipe = extractor._parse_with_llm(text, "用户粘贴")
        
        if recipe.get("error"):
            print(f"\n❌ {recipe['error']}")
        else:
            print("\n📋 提取结果:")
            print(json.dumps(recipe, ensure_ascii=False, indent=2))
    
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()
