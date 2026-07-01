import uuid
from datetime import datetime

sessions = {}

def create_session() -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "history": [],
        "todo_list": [],
        "weather_cache": {
            "data": None,
            "fetched_at": None
        }
    }
    return session_id

def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        raise ValueError(f"Session {session_id} 不存在")
    return sessions[session_id]

def add_message(session_id: str, role: str, content: str):
    session = get_session(session_id)
    session["history"].append({
        "role": role,
        "content": content
    })