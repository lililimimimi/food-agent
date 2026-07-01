import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1"
)

def call_llm(messages: list, tools: list = None) -> dict:
    params = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": messages,
    }
    if tools:
        params["tools"] = tools

    response = client.chat.completions.create(**params)
    return response