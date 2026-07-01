import json
from agent.llm_client import call_llm
from agent.session import get_session, add_message
from agent.context import build_context, summarize_if_needed
from agent.tools.registry import TOOL_REGISTRY, get_tools_schema

MAX_LOOP = 5

SYSTEM_PROMPT = """你是一个专业的食物决策助手,帮助用户解决"今天吃什么"的问题。

你有以下工具可以使用:
- get_weather: 查询城市天气,辅助饮食决策
- random_pick: 根据条件随机推荐食物
- search_food: 查询食物详细信息(价格/热量等)
- calculator: 计算预算或热量
- add_todo: 记录今天吃了什么
- list_todo: 查看饮食历史记录
- complete_todo: 标记某条记录完成

决策原则:
1. 先了解用户的约束条件(预算/天气/口味偏好)
2. 如果用户提到城市,必须先调用get_weather查天气
3. 有了天气和约束条件后,必须调用random_pick工具推荐食物
4. 禁止自己编造食物推荐,所有推荐必须来自random_pick工具的结果
5. 推荐后询问用户是否要用add_todo记录到今天的饮食历史

重要:
- 推荐食物时永远调用random_pick,不要自己列举食物
- 用户说"换一个"时,再次调用random_pick

回复风格:
- 轻松活泼,像朋友推荐一样自然
- 给出推荐理由,不要只说结果
- 适当加入emoji让回复更生动
"""

def run_agent(session_id: str, user_input: str) -> str:
    session = get_session(session_id)

    summarize_if_needed(session_id)
    add_message(session_id, "user", user_input)

    history = build_context(session_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    tools = get_tools_schema()

    loop_count = 0

    while loop_count < MAX_LOOP:
        loop_count += 1
        print(f"\n--- Loop {loop_count} ---")

        response = call_llm(messages, tools)
        message = response.choices[0].message

        if message.tool_calls:
            # 有工具调用时才打印Thought
            if message.content:
                print(f"[Thought] {message.content}")

            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"[Action] 调用工具: {tool_name}, 参数: {tool_args}")

                observation = execute_tool(tool_name, tool_args, session)
                print(f"[Observation] {observation}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation
                })

        else:
            # 纯对话直接返回,不打印多余内容
            final_answer = message.content
            add_message(session_id, "assistant", final_answer)
            return final_answer

    return "已达到最大推理次数,请重新提问"


def execute_tool(tool_name: str, tool_args: dict, session: dict) -> str:
    if tool_name not in TOOL_REGISTRY:
        return f"工具不存在: {tool_name}"

    tool = TOOL_REGISTRY[tool_name]
    fn = tool["fn"]

    try:
        if tool_name in ["get_weather", "add_todo", "list_todo", "complete_todo"]:
            return fn(session=session, **tool_args)
        else:
            return fn(**tool_args)
    except Exception as e:
        return f"工具执行失败: {str(e)}"