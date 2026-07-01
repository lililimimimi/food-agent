from agent.session import get_session

MAX_TURNS = 10

def build_context(session_id: str) -> list:
    session = get_session(session_id)
    history = session["history"]

    # 超过最大轮次,只保留最近MAX_TURNS条
    if len(history) > MAX_TURNS:
        history = history[-MAX_TURNS:]

    return history

def summarize_if_needed(session_id: str):
    session = get_session(session_id)
    history = session["history"]

    # 超过最大轮次时,把最早的几条压缩成一句摘要
    if len(history) > MAX_TURNS:
        old = history[:-MAX_TURNS]
        summary_text = f"[早期对话摘要]: 共{len(old)}条历史记录已压缩"
        session["history"] = [
            {"role": "system", "content": summary_text}
        ] + history[-MAX_TURNS:]