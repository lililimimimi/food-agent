from agent.tools.calculator import calculator
from agent.tools.weather import get_weather
from agent.tools.todo import add_todo, list_todo, complete_todo
from agent.tools.random_pick import random_pick
from agent.tools.search_food import search_food

TOOL_REGISTRY = {
    "calculator": {
        "name": "calculator",
        "description": "用于数学计算,支持加减乘除等基本运算",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式,例如 '(10+20)*3'"
                }
            },
            "required": ["expression"]
        },
        "fn": calculator
    },
    "get_weather": {
        "name": "get_weather",
        "description": "查询指定城市的实时天气,用于辅助饮食决策",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称,例如'海口'、'北京'"
                }
            },
            "required": ["city"]
        },
        "fn": get_weather
    },
    "add_todo": {
        "name": "add_todo",
        "description": "添加一条饮食记录或待办事项",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "待办内容,例如'今天吃了火锅'"
                }
            },
            "required": ["content"]
        },
        "fn": add_todo
    },
    "list_todo": {
        "name": "list_todo",
        "description": "查看当前所有饮食记录和待办事项",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "fn": list_todo
    },
    "complete_todo": {
        "name": "complete_todo",
        "description": "标记某条待办事项为已完成",
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "待办事项的序号,从1开始"
                }
            },
            "required": ["index"]
        },
        "fn": complete_todo
    },
    "random_pick": {
        "name": "random_pick",
        "description": "根据条件(价格/辣度/天气/类型)随机推荐一个食物",
        "parameters": {
            "type": "object",
            "properties": {
                "max_price": {
                    "type": "integer",
                    "description": "最高预算,单位元,例如50"
                },
                "spicy": {
                    "type": "boolean",
                    "description": "是否要辣的,true=要辣,false=不要辣"
                },
                "weather": {
                    "type": "string",
                    "description": "当前天气,例如'rainy'、'sunny'、'cold'"
                },
                "food_type": {
                    "type": "string",
                    "description": "食物类型,例如'快餐'、'面食'、'热食'"
                }
            }
        },
        "fn": random_pick
    },
    "search_food": {
        "name": "search_food",
        "description": "查询食物的价格、热量等详细信息",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "食物名称,例如'火锅'"
                },
                "food_type": {
                    "type": "string",
                    "description": "食物类型,例如'快餐'、'面食'"
                },
                "max_price": {
                    "type": "integer",
                    "description": "最高价格,单位元"
                },
                "max_calorie": {
                    "type": "integer",
                    "description": "最高热量,单位kcal"
                }
            }
        },
        "fn": search_food
    }
}

def get_tools_schema() -> list:
    """返回给LLM的工具Schema列表"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        }
        for tool in TOOL_REGISTRY.values()
    ]