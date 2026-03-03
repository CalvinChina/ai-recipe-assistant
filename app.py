"""
AI 菜谱助手 - Web UI
"""

import os
import gradio as gr
from dotenv import load_dotenv
from zhipuai import ZhipuAI
import json

from recipe_parser import parse_recipe
from image_analyzer import ImageAnalyzer
from conversation import ConversationAssistant

load_dotenv()

# 初始化
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
image_analyzer = ImageAnalyzer()
chat_assistant = ConversationAssistant()


def chat_fn(message, history):
    """对话功能"""
    response = chat_assistant.chat(message)
    return response


def parse_recipe_fn(text):
    """解析菜谱文本"""
    if not text.strip():
        return "请输入菜谱内容"
    
    try:
        result = parse_recipe(client, text)
        if result:
            return json.dumps(result, ensure_ascii=False, indent=2)
        return "解析失败"
    except Exception as e:
        return f"错误: {str(e)}"


def analyze_image_fn(image):
    """分析图片"""
    if image is None:
        return "请上传图片"
    
    try:
        # Gradio 返回的是文件路径
        result = image_analyzer.analyze_dish(image)
        if isinstance(result, list):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"错误: {str(e)}"


# 创建界面
with gr.Blocks(title="🍳 AI 菜谱助手") as demo:
    gr.Markdown("# 🍳 AI 菜谱助手")
    gr.Markdown("基于智谱 GLM-4 的智能菜谱助手")
    
    with gr.Tabs():
        # Tab 1: 对话
        with gr.TabItem("💬 对话"):
            gr.Markdown("与 AI 菜谱助手聊天，询问任何烹饪问题")
            chat_interface = gr.ChatInterface(
                fn=chat_fn,
                title="",
                examples=[
                    "红烧肉怎么做？",
                    "番茄炒蛋的秘诀是什么？",
                    "有什么适合夏天吃的凉菜？",
                    "如何让牛肉更嫩？"
                ]
            )
        
        # Tab 2: 菜谱解析
        with gr.TabItem("📝 菜谱解析"):
            gr.Markdown("粘贴菜谱文本，自动提取结构化信息")
            with gr.Row():
                with gr.Column():
                    recipe_input = gr.Textbox(
                        label="菜谱内容",
                        placeholder="粘贴菜谱文本...\n\n例如：\n红烧肉\n\n食材：五花肉500克，冰糖30克...\n\n做法：\n1. 五花肉切块...",
                        lines=10
                    )
                    parse_btn = gr.Button("🔍 解析菜谱", variant="primary")
                with gr.Column():
                    recipe_output = gr.Code(
                        label="结构化结果",
                        language="json",
                        lines=15
                    )
            parse_btn.click(parse_recipe_fn, inputs=recipe_input, outputs=recipe_output)
        
        # Tab 3: 图片识别
        with gr.TabItem("📷 图片识别"):
            gr.Markdown("上传菜品图片，AI 自动识别")
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(label="上传图片", type="filepath")
                    analyze_btn = gr.Button("🔍 识别菜品", variant="primary")
                with gr.Column():
                    image_output = gr.Code(
                        label="识别结果",
                        language="json",
                        lines=15
                    )
            analyze_btn.click(analyze_image_fn, inputs=image_input, outputs=image_output)
    
    gr.Markdown("""
    ---
    ### 📌 使用说明
    - **对话**: 直接提问烹饪相关问题
    - **菜谱解析**: 粘贴菜谱文本，自动提取食材、步骤等
    - **图片识别**: 上传菜品照片，AI 识别菜名和食材
    
    Powered by [智谱 AI](https://open.bigmodel.cn)
    """)


if __name__ == "__main__":
    demo.launch()
