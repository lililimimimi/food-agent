from agent.tools.food_db import FOOD_DB

def search_food(name: str = None, food_type: str = None, max_price: int = None, max_calorie: int = None) -> str:
    """根据条件查询食物信息"""

    candidates = list(FOOD_DB.values())

    # 按名字精确查询
    if name is not None:
        if name in FOOD_DB:
            food = FOOD_DB[name]
            return (
                f"【{food['name']}】\n"
                f"价格: ¥{food['price']} | "
                f"热量: {food['calorie']}kcal | "
                f"类型: {food['type']} | "
                f"辣: {'是' if food['spicy'] else '否'}\n"
                f"适合天气: {', '.join(food['weather_tags'])}\n"
                f"简介: {food['description']}"
            )
        else:
            return f"找不到食物: {name}"

    # 按条件筛选
    if food_type is not None:
        candidates = [f for f in candidates if f["type"] == food_type]

    if max_price is not None:
        candidates = [f for f in candidates if f["price"] <= max_price]

    if max_calorie is not None:
        candidates = [f for f in candidates if f["calorie"] <= max_calorie]

    if not candidates:
        return "没有符合条件的食物,请放宽筛选条件"

    result = f"找到{len(candidates)}种食物:\n"
    for f in candidates:
        result += (
            f"- 【{f['name']}】"
            f"¥{f['price']} | "
            f"{f['calorie']}kcal | "
            f"{f['description']}\n"
        )
    return result