import random
from agent.tools.food_db import FOOD_DB

def random_pick(
    max_price: int = None,
    spicy: bool = None,
    weather: str = None,
    food_type: str = None
) -> str:
    """根据条件筛选后随机推荐一个食物"""
    
    candidates = list(FOOD_DB.values())

    # 按价格筛选
    if max_price is not None:
        candidates = [f for f in candidates if f["price"] <= max_price]

    # 按辣度筛选
    if spicy is not None:
        candidates = [f for f in candidates if f["spicy"] == spicy]

    # 按天气筛选
    if weather is not None:
        candidates = [f for f in candidates if weather in f["weather_tags"]]

    # 按类型筛选
    if food_type is not None:
        candidates = [f for f in candidates if f["type"] == food_type]

    if not candidates:
        return "没有符合条件的食物,请放宽筛选条件"

    picked = random.choice(candidates)
    return (
        f"为你随机推荐: 【{picked['name']}】\n"
        f"价格: ¥{picked['price']} | "
        f"热量: {picked['calorie']}kcal | "
        f"辣: {'是' if picked['spicy'] else '否'}\n"
        f"推荐理由: {picked['description']}"
    )