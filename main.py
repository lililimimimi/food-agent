from agent.session import create_session
from agent.runtime import run_agent

def main():
    print("🍜 Food Decision Agent 启动!")
    print("输入 'exit' 退出, 输入 'new' 开启新session\n")

    session_id = create_session()
    print(f"当前Session: {session_id}\n")

    while True:
        user_input = input("你: ").strip()

        if not user_input:
            continue

        if user_input == "exit":
            print("再见!")
            break

        if user_input == "new":
            session_id = create_session()
            print(f"新Session已创建: {session_id}\n")
            continue

        answer = run_agent(session_id, user_input)
        print(f"\nAgent: {answer}\n")

if __name__ == "__main__":
    main()