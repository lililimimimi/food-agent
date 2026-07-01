def calculator(expression: str) -> str:
    try:
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算失败: {str(e)}"