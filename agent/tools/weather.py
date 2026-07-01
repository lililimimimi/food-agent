import time
import requests

def get_weather(city: str, session: dict) -> str:
    cache = session["weather_cache"]
    now = time.time()

    # 有缓存且30分钟内,直接返回
    if cache["data"] and cache["fetched_at"] and (now - cache["fetched_at"] < 1800):
        return f"(缓存) {cache['data']}"

    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        response = requests.get(url, timeout=10)
        data = response.json()

        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["lang_zh"][0]["value"]
        humidity = current["humidity"]

        result = f"{city}天气: {desc}, {temp}°C, 湿度{humidity}%"

        # 写入缓存
        cache["data"] = result
        cache["fetched_at"] = time.time()

        return result

    except Exception as e:
        return f"天气查询失败: {str(e)},请直接告诉我当前天气"