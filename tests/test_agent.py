import pytest
from agent.session import create_session, get_session
from agent.runtime import run_agent
from agent.tools.calculator import calculator
from agent.tools.weather import get_weather
from agent.tools.todo import add_todo, list_todo, complete_todo
from agent.tools.random_pick import random_pick
from agent.tools.search_food import search_food

# ============ 工具单元测试 ============

def test_calculator_budget():
    """预算计算:100块买了火锅80块,还剩多少"""
    result = calculator("100-80")
    assert "20" in result

def test_calculator_calorie():
    """热量计算:火锅800卡+沙拉200卡总热量"""
    result = calculator("800+200")
    assert "1000" in result

def test_calculator_split_bill():
    """AA制:三个人吃火锅240块,每人多少"""
    result = calculator("240/3")
    assert "80" in result

def test_calculator_error():
    """非法表达式"""
    result = calculator("abc+1")
    assert "失败" in result

def test_random_pick_no_filter():
    """无条件随机推荐"""
    result = random_pick()
    assert "推荐" in result

def test_random_pick_with_price():
    """预算筛选"""
    result = random_pick(max_price=20)
    assert "推荐" in result or "没有符合条件" in result

def test_random_pick_with_weather():
    """天气筛选"""
    result = random_pick(weather="rainy")
    assert "推荐" in result

def test_random_pick_no_match():
    """无匹配结果"""
    result = random_pick(max_price=1)
    assert "没有符合条件" in result

def test_search_food_by_name():
    """按名字查食物"""
    result = search_food(name="火锅")
    assert "火锅" in result
    assert "价格" in result

def test_search_food_not_found():
    """查不存在的食物"""
    result = search_food(name="不存在的食物")
    assert "找不到" in result

def test_search_food_by_price():
    """按价格筛选"""
    result = search_food(max_price=20)
    assert "找到" in result

# ============ Session测试 ============

def test_session_create():
    """创建session"""
    session_id = create_session()
    assert session_id is not None
    session = get_session(session_id)
    assert session["history"] == []
    assert session["todo_list"] == []

def test_session_isolation():
    """session隔离测试:两个session互不影响"""
    session_id_1 = create_session()
    session_id_2 = create_session()

    session_1 = get_session(session_id_1)
    session_2 = get_session(session_id_2)

    # session1加一条todo
    add_todo(session=session_1, content="session1吃了火锅")

    # session2加另一条todo
    add_todo(session=session_2, content="session2吃了寿司")

    # 验证互不影响
    assert len(session_1["todo_list"]) == 1
    assert len(session_2["todo_list"]) == 1
    assert session_1["todo_list"][0]["content"] == "session1吃了火锅"
    assert session_2["todo_list"][0]["content"] == "session2吃了寿司"

def test_session_not_found():
    """查询不存在的session"""
    with pytest.raises(ValueError):
        get_session("不存在的session_id")

# ============ Todo测试 ============

def test_todo_add_and_list():
    """添加并查看todo"""
    session_id = create_session()
    session = get_session(session_id)

    add_todo(session=session, content="今天吃了拉面")
    result = list_todo(session=session)
    assert "拉面" in result

def test_todo_complete():
    """完成todo"""
    session_id = create_session()
    session = get_session(session_id)

    add_todo(session=session, content="今天吃了饺子")
    result = complete_todo(session=session, index=1)
    assert "完成" in result
    assert session["todo_list"][0]["done"] == True

def test_todo_complete_invalid_index():
    """完成不存在的todo"""
    session_id = create_session()
    session = get_session(session_id)
    result = complete_todo(session=session, index=99)
    assert "没有" in result

def test_todo_empty():
    """空todo列表"""
    session_id = create_session()
    session = get_session(session_id)
    result = list_todo(session=session)
    assert "暂无" in result

# ============ Agent完整链路测试 ============

def test_agent_basic_reply():
    """基本对话,无需工具"""
    session_id = create_session()
    result = run_agent(session_id, "你好")
    assert result is not None
    assert len(result) > 0

def test_agent_random_pick():
    """触发random_pick工具"""
    session_id = create_session()
    result = run_agent(session_id, "随机给我推荐一个食物,预算50块")
    assert result is not None

def test_agent_followup():
    """追问测试:上一轮推荐后换一个"""
    session_id = create_session()
    run_agent(session_id, "随机推荐一个食物")
    result = run_agent(session_id, "不想吃这个,换一个")
    assert result is not None

def test_agent_session_memory():
    """session记忆测试:记住上下文"""
    session_id = create_session()
    run_agent(session_id, "我预算只有30块")
    result = run_agent(session_id, "帮我推荐吃什么")
    assert result is not None

def test_agent_todo_record():
    """记录饮食历史"""
    session_id = create_session()
    run_agent(session_id, "帮我记录今天吃了火锅")
    session = get_session(session_id)
    assert len(session["todo_list"]) > 0