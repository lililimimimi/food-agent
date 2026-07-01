def add_todo(session: dict, content: str) -> str:
    try:
        session["todo_list"].append({
            "content": content,
            "done": False
        })
        return f"已添加待办: {content}"
    except Exception as e:
        return f"添加失败: {str(e)}"

def list_todo(session: dict) -> str:
    todos = session["todo_list"]
    if not todos:
        return "暂无待办事项"
    
    result = "当前待办列表:\n"
    for i, todo in enumerate(todos, 1):
        status = "✅" if todo["done"] else "⬜"
        result += f"{i}. {status} {todo['content']}\n"
    return result

def complete_todo(session: dict, index: int) -> str:
    todos = session["todo_list"]
    if index < 1 or index > len(todos):
        return f"没有第{index}条待办"
    
    todos[index - 1]["done"] = True
    return f"已完成: {todos[index - 1]['content']}"